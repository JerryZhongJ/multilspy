"""
This file contains the main interface and the public API for multilspy. 
The abstract class LanguageServer provides a factory method, creator that is 
intended for creating instantiations of language specific clients.
The details of Language Specific configuration are not exposed to the user.
"""

import asyncio
import dataclasses
import logging
import os
import pathlib
import threading
from contextlib import asynccontextmanager, contextmanager
from pathlib import PurePath
from typing import AsyncIterator, Dict, Iterator, List, Optional, Tuple, Union

from . import multilspy_types
from .lsp_protocol_handler import lsp_types as LSPTypes
from .lsp_protocol_handler.lsp_constants import LSPConstants
from .lsp_protocol_handler.server import LanguageServerHandler, ProcessLaunchInfo
from .multilspy_config import Language, MultilspyConfig
from .multilspy_exceptions import MultilspyException
from .multilspy_logger import MultilspyLogger
from .multilspy_utils import FileUtils, PathUtils, TextUtils
from .type_helpers import ensure_all_methods_implemented


@dataclasses.dataclass
class LSPFileBuffer:
    """
    This class is used to store the contents of an open LSP file in memory.
    """

    # uri of the file
    uri: str

    # The contents of the file
    contents: str

    # The version of the file
    version: int

    # The language id of the file
    language_id: str

    # reference count of the file
    ref_count: int

    def is_referenced(self):
        return self.ref_count > 0


class LanguageServer:
    """
    The LanguageServer class provides a language agnostic interface to the Language Server Protocol.
    It is used to communicate with Language Servers of different programming languages.
    """

    @classmethod
    def create(
        cls,
        config: MultilspyConfig,
        repository_root_path: str,
        logger: Optional[logging.Logger] = None,
    ) -> "LanguageServer":
        """
        Creates a language specific LanguageServer instance based on the given configuration, and appropriate settings for the programming language.

        If language is Java, then ensure that jdk-17.0.6 or higher is installed, `java` is in PATH, and JAVA_HOME is set to the installation directory.
        If language is JS/TS, then ensure that node (v18.16.0 or higher) is installed and in PATH.

        :param repository_root_path: The root path of the repository.
        :param config: The Multilspy configuration.
        :param logger: The logger to use.

        :return LanguageServer: A language specific LanguageServer instance.
        """
        if logger is None:
            _logger = MultilspyLogger(logging.getLogger("multilspy"))
        else:
            _logger = MultilspyLogger(logger)
        if config.code_language == Language.PYTHON:
            from multilspy.language_servers.jedi_language_server.jedi_server import (
                JediServer,
            )

            return JediServer(config, _logger, repository_root_path)
        elif config.code_language == Language.JAVA:
            from multilspy.language_servers.eclipse_jdtls.eclipse_jdtls import (
                EclipseJDTLS,
            )

            return EclipseJDTLS(config, _logger, repository_root_path)
        elif config.code_language == Language.RUST:
            from multilspy.language_servers.rust_analyzer.rust_analyzer import (
                RustAnalyzer,
            )

            return RustAnalyzer(config, _logger, repository_root_path)
        elif config.code_language == Language.CSHARP:
            from multilspy.language_servers.omnisharp.omnisharp import OmniSharp

            return OmniSharp(config, _logger, repository_root_path)
        elif config.code_language in [Language.TYPESCRIPT, Language.JAVASCRIPT]:
            from multilspy.language_servers.typescript_language_server.typescript_language_server import (
                TypeScriptLanguageServer,
            )

            return TypeScriptLanguageServer(config, _logger, repository_root_path)
        else:
            _logger.log(
                f"Language {config.code_language} is not supported", logging.ERROR
            )
            raise MultilspyException(
                f"Language {config.code_language} is not supported"
            )

    def __init__(
        self,
        config: MultilspyConfig,
        logger: MultilspyLogger,
        repository_root_path: str,
        process_launch_info: ProcessLaunchInfo,
        language_id: str,
    ):
        """
        Initializes a LanguageServer instance.

        Do not instantiate this class directly. Use `LanguageServer.create` method instead.

        :param config: The Multilspy configuration.
        :param logger: The logger to use.
        :param repository_root_path: The root path of the repository.
        :param cmd: Each language server has a specific command used to start the server.
                    This parameter is the command to launch the language server process.
                    The command must pass appropriate flags to the binary, so that it runs in the stdio mode,
                    as opposed to HTTP, TCP modes supported by some language servers.
        """
        if type(self) == LanguageServer:
            raise MultilspyException(
                "LanguageServer is an abstract class and cannot be instantiated directly. Use LanguageServer.create method instead."
            )

        self.logger = logger
        self.server_started = False
        self.repository_root_path: str = repository_root_path
        self.completions_available = asyncio.Event()

        if config.trace_lsp_communication:

            def logging_fn(source, target, msg):
                self.logger.log(f"LSP: {source} -> {target}: {str(msg)}", logging.INFO)

        else:

            def logging_fn(source, target, msg):
                pass

        # cmd is obtained from the child classes, which provide the language specific command to start the language server
        # LanguageServerHandler provides the functionality to start the language server and communicate with it
        self.server: LanguageServerHandler = LanguageServerHandler(
            process_launch_info, logger=logging_fn
        )

        self.language_id = language_id
        self.file_buffers: Dict[str, LSPFileBuffer] = {}

    @asynccontextmanager
    async def running(self) -> AsyncIterator["LanguageServer"]:
        """
        Starts the Language Server and yields the LanguageServer instance.

        Usage:
        ```
        async with lsp.running():
            # LanguageServer has been initialized and ready to serve requests
            await lsp.request_definition(...)
            await lsp.request_references(...)
            # Shutdown the LanguageServer on exit from scope
        # LanguageServer has been shutdown
        ```
        """
        await self.start()
        try:
            yield self
        finally:
            await self.stop()

    async def start(self):
        self.server_started = True

    async def stop(self):
        self.server_started = False
        await self.server.shutdown()
        await self.server.stop()

    @contextmanager
    def file_opened(self, relative_file_path: str) -> Iterator[None]:
        """
        Open a file in the Language Server. This is required before making any requests to the Language Server.

        :param relative_file_path: The relative path of the file to open.
        """

        if not self.server_started:
            self.logger.log(
                "open_file called before Language Server started",
                logging.ERROR,
            )
            raise MultilspyException("Language Server not started")
        absolute_file_path = str(
            PurePath(self.repository_root_path, relative_file_path)
        )
        uri = pathlib.Path(absolute_file_path).as_uri()
        if uri in self.file_buffers:
            file_buffer = self.file_buffers[uri]
        else:
            file_buffer = LSPFileBuffer(uri, "", 0, self.language_id, 0)
            self.file_buffers[uri] = file_buffer
        if not file_buffer.is_referenced():
            contents = FileUtils.read_file(self.logger, absolute_file_path)
            if contents != file_buffer.contents:
                file_buffer.version += 1
                file_buffer.contents = contents
            self.server.notify.did_open_text_document(
                LSPTypes.DidOpenTextDocumentParams.model_validate(
                    {
                        LSPConstants.TEXT_DOCUMENT: {
                            LSPConstants.URI: uri,
                            LSPConstants.LANGUAGE_ID: self.language_id,
                            LSPConstants.VERSION: file_buffer.version,
                            LSPConstants.TEXT: contents,
                        }
                    }
                )
            )

        file_buffer.ref_count += 1
        try:
            yield
        finally:
            file_buffer.ref_count -= 1
            if not file_buffer.is_referenced():
                self.server.notify.did_close_text_document(
                    LSPTypes.DidCloseTextDocumentParams.model_validate(
                        {
                            LSPConstants.TEXT_DOCUMENT: {
                                LSPConstants.URI: uri,
                            }
                        }
                    )
                )

    def insert_text_at_position(
        self, relative_file_path: str, line: int, column: int, text_to_be_inserted: str
    ) -> multilspy_types.Position:
        """
        Insert text at the given line and column in the given file and return
        the updated cursor position after inserting the text.

        :param relative_file_path: The relative path of the file to open.
        :param line: The line number at which text should be inserted.
        :param column: The column number at which text should be inserted.
        :param text_to_be_inserted: The text to insert.
        """
        if not self.server_started:
            self.logger.log(
                "insert_text_at_position called before Language Server started",
                logging.ERROR,
            )
            raise MultilspyException("Language Server not started")

        absolute_file_path = str(
            PurePath(self.repository_root_path, relative_file_path)
        )
        uri = pathlib.Path(absolute_file_path).as_uri()

        # Ensure the file is open
        assert uri in self.file_buffers

        file_buffer = self.file_buffers[uri]
        file_buffer.version += 1
        change_index = TextUtils.get_index_from_line_col(
            file_buffer.contents, line, column
        )
        file_buffer.contents = (
            file_buffer.contents[:change_index]
            + text_to_be_inserted
            + file_buffer.contents[change_index:]
        )
        self.server.notify.did_change_text_document(
            LSPTypes.DidChangeTextDocumentParams.model_validate(
                {
                    LSPConstants.TEXT_DOCUMENT: {
                        LSPConstants.VERSION: file_buffer.version,
                        LSPConstants.URI: file_buffer.uri,
                    },
                    LSPConstants.CONTENT_CHANGES: [
                        {
                            LSPConstants.RANGE: {
                                "start": {"line": line, "character": column},
                                "end": {"line": line, "character": column},
                            },
                            LSPConstants.TEXT: text_to_be_inserted,
                        }
                    ],
                }
            )
        )
        new_l, new_c = TextUtils.get_updated_position_from_line_and_column_and_edit(
            line, column, text_to_be_inserted
        )
        return multilspy_types.Position(line=new_l, character=new_c)

    def delete_text_between_positions(
        self,
        relative_file_path: str,
        start: multilspy_types.Position,
        end: multilspy_types.Position,
    ) -> str:
        """
        Delete text between the given start and end positions in the given file and return the deleted text.
        """
        if not self.server_started:
            self.logger.log(
                "insert_text_at_position called before Language Server started",
                logging.ERROR,
            )
            raise MultilspyException("Language Server not started")

        absolute_file_path = str(
            PurePath(self.repository_root_path, relative_file_path)
        )
        uri = pathlib.Path(absolute_file_path).as_uri()

        # Ensure the file is open
        assert uri in self.file_buffers

        file_buffer = self.file_buffers[uri]
        file_buffer.version += 1
        del_start_idx = TextUtils.get_index_from_line_col(
            file_buffer.contents, start.line, start.character
        )
        del_end_idx = TextUtils.get_index_from_line_col(
            file_buffer.contents, end.line, end.character
        )
        deleted_text = file_buffer.contents[del_start_idx:del_end_idx]
        file_buffer.contents = (
            file_buffer.contents[:del_start_idx] + file_buffer.contents[del_end_idx:]
        )
        self.server.notify.did_change_text_document(
            LSPTypes.DidChangeTextDocumentParams.model_validate(
                {
                    LSPConstants.TEXT_DOCUMENT: {
                        LSPConstants.VERSION: file_buffer.version,
                        LSPConstants.URI: file_buffer.uri,
                    },
                    LSPConstants.CONTENT_CHANGES: [
                        {
                            LSPConstants.RANGE: {"start": start, "end": end},
                            LSPConstants.TEXT: "",
                        }
                    ],
                }
            )
        )
        return deleted_text

    def get_open_file_text(self, relative_file_path: str) -> str:
        """
        Get the contents of the given opened file as per the Language Server.

        :param relative_file_path: The relative path of the file to open.
        """
        if not self.server_started:
            self.logger.log(
                "get_open_file_text called before Language Server started",
                logging.ERROR,
            )
            raise MultilspyException("Language Server not started")

        absolute_file_path = str(
            PurePath(self.repository_root_path, relative_file_path)
        )
        uri = pathlib.Path(absolute_file_path).as_uri()

        # Ensure the file is open
        assert uri in self.file_buffers

        file_buffer = self.file_buffers[uri]
        return file_buffer.contents

    async def request_definition(
        self, relative_file_path: str, line: int, column: int
    ) -> List[multilspy_types.Location]:
        """
        Raise a [textDocument/definition](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_definition) request to the Language Server
        for the symbol at the given line and column in the given file. Wait for the response and return the result.

        :param relative_file_path: The relative path of the file that has the symbol for which definition should be looked up
        :param line: The line number of the symbol
        :param column: The column number of the symbol

        :return List[multilspy_types.Location]: A list of locations where the symbol is defined
        """

        if not self.server_started:
            self.logger.log(
                "find_function_definition called before Language Server started",
                logging.ERROR,
            )
            raise MultilspyException("Language Server not started")

        with self.file_opened(relative_file_path):
            # sending request to the language server and waiting for response
            response = await self.server.send.definition(
                LSPTypes.DefinitionParams.model_validate(
                    {
                        LSPConstants.TEXT_DOCUMENT: {
                            LSPConstants.URI: pathlib.Path(
                                str(
                                    PurePath(
                                        self.repository_root_path, relative_file_path
                                    )
                                )
                            ).as_uri()
                        },
                        LSPConstants.POSITION: {
                            LSPConstants.LINE: line,
                            LSPConstants.CHARACTER: column,
                        },
                    }
                )
            )

        ret: List[multilspy_types.Location] = []
        if isinstance(response, list):
            # response is either of type Location[] or LocationLink[]
            for item in response:
                if isinstance(item, LSPTypes.Location):
                    absolute_path = PathUtils.uri_to_path(item.uri)
                    relative_path = PurePath(
                        os.path.relpath(absolute_path, self.repository_root_path)
                    ).name
                    ret.append(
                        multilspy_types.Location(
                            **item.model_dump(),
                            absolutePath=absolute_path,
                            relativePath=relative_path,
                        )
                    )
                elif isinstance(item, LSPTypes.LocationLink):

                    uri = item.targetUri
                    absolutePath = PathUtils.uri_to_path(uri)
                    relativePath = PurePath(
                        os.path.relpath(absolutePath, self.repository_root_path)
                    ).name

                    range = multilspy_types.Range.model_validate(item.targetRange)
                    ret.append(
                        multilspy_types.Location(
                            uri=uri,
                            range=range,
                            absolutePath=absolutePath,
                            relativePath=relativePath,
                        )
                    )
                else:
                    assert False, f"Unexpected response from Language Server: {item}"
        elif isinstance(response, LSPTypes.Location):
            # response is of type Location
            absolute_path = PathUtils.uri_to_path(response.uri)
            relative_path = PurePath(
                os.path.relpath(absolute_path, self.repository_root_path)
            ).name
            ret.append(
                multilspy_types.Location(
                    **response.model_dump(),
                    absolutePath=absolute_path,
                    relativePath=relative_path,
                )
            )
        else:
            assert False, f"Unexpected response from Language Server: {response}"

        return ret

    async def request_references(
        self, relative_file_path: str, line: int, column: int
    ) -> List[multilspy_types.Location]:
        """
        Raise a [textDocument/references](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_references) request to the Language Server
        to find references to the symbol at the given line and column in the given file. Wait for the response and return the result.

        :param relative_file_path: The relative path of the file that has the symbol for which references should be looked up
        :param line: The line number of the symbol
        :param column: The column number of the symbol

        :return List[multilspy_types.Location]: A list of locations where the symbol is referenced
        """

        if not self.server_started:
            self.logger.log(
                "find_all_callers_of_function called before Language Server started",
                logging.ERROR,
            )
            raise MultilspyException("Language Server not started")

        with self.file_opened(relative_file_path):
            # sending request to the language server and waiting for response
            response = await self.server.send.references(
                LSPTypes.ReferenceParams.model_validate(
                    {
                        "context": {"includeDeclaration": False},
                        "textDocument": {
                            "uri": pathlib.Path(
                                os.path.join(
                                    self.repository_root_path, relative_file_path
                                )
                            ).as_uri()
                        },
                        "position": {"line": line, "character": column},
                    }
                )
            )

        ret: List[multilspy_types.Location] = []
        if response is None:
            return ret
        for item in response:

            absolute_path = PathUtils.uri_to_path(item.uri)
            relative_path = PurePath(
                os.path.relpath(absolute_path, self.repository_root_path)
            ).name
            ret.append(
                multilspy_types.Location(
                    **item.model_dump(),
                    absolutePath=absolute_path,
                    relativePath=relative_path,
                )
            )
        return ret

    async def request_completions(
        self,
        relative_file_path: str,
        line: int,
        column: int,
        allow_incomplete: bool = False,
    ) -> List[multilspy_types.CompletionItem]:
        """
        Raise a [textDocument/completion](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_completion) request to the Language Server
        to find completions at the given line and column in the given file. Wait for the response and return the result.

        :param relative_file_path: The relative path of the file that has the symbol for which completions should be looked up
        :param line: The line number of the symbol
        :param column: The column number of the symbol

        :return List[multilspy_types.CompletionItem]: A list of completions
        """
        with self.file_opened(relative_file_path):
            open_file_buffer = self.file_buffers[
                pathlib.Path(
                    os.path.join(self.repository_root_path, relative_file_path)
                ).as_uri()
            ]
            completion_params = LSPTypes.CompletionParams.model_validate(
                {
                    "position": {"line": line, "character": column},
                    "textDocument": {"uri": open_file_buffer.uri},
                    "context": {"triggerKind": LSPTypes.CompletionTriggerKind.Invoked},
                }
            )
            response: Optional[LSPTypes.CompletionList] = None

            num_retries = 0
            while response is None or (response.isIncomplete and num_retries < 30):
                await self.completions_available.wait()
                tmp: Optional[
                    List[LSPTypes.CompletionItem] | LSPTypes.CompletionList
                ] = await self.server.send.completion(completion_params)
                if isinstance(tmp, list):
                    response = LSPTypes.CompletionList.model_validate(
                        {"items": tmp, "isIncomplete": False}
                    )
                num_retries += 1

            # TODO: Understand how to appropriately handle `isIncomplete`
            if response is None or (response.isIncomplete and not (allow_incomplete)):
                return []
            responses: List[LSPTypes.CompletionItem] = response.items

            completions_list: List[multilspy_types.CompletionItem] = []

            for item in responses:

                if not item.kind:
                    continue
                # TODO: Handle the case when the completion is a keyword
                if item.kind == LSPTypes.CompletionItemKind.Keyword:
                    continue
                kind: multilspy_types.CompletionItemKind = item.kind  # type: ignore
                if item.labelDetails is None:
                    completion_item = multilspy_types.CompletionItem(
                        completionText=item.label, kind=kind, detail=item.detail
                    )

                elif item.insertText:
                    completion_item = multilspy_types.CompletionItem(
                        completionText=item.insertText,
                        kind=kind,
                        detail=item.detail,
                    )
                elif item.textEdit:
                    assert isinstance(item.textEdit, LSPTypes.TextEdit)
                    new_dot_lineno, new_dot_colno = (
                        completion_params.position.line,
                        completion_params.position.character,
                    )
                    assert all(
                        (
                            item.textEdit.range.start.line == new_dot_lineno,
                            item.textEdit.range.start.character == new_dot_colno,
                            item.textEdit.range.start.line
                            == item.textEdit.range.end.line,
                            item.textEdit.range.start.character
                            == item.textEdit.range.end.character,
                        )
                    )
                    completion_item = multilspy_types.CompletionItem(
                        completionText=item.textEdit.newText,
                        kind=kind,
                        detail=item.detail,
                    )

                else:
                    assert False

                completions_list.append(completion_item)
            return completions_list
            # return [
            #     json.loads(json_repr)
            #     for json_repr in set(
            #         [json.dumps(item, sort_keys=True) for item in completions_list]
            #     )
            # ]

    async def request_document_symbols(self, relative_file_path: str) -> Tuple[
        List[multilspy_types.UnifiedSymbolInformation],
        Optional[List[multilspy_types.TreeRepr]],
    ]:
        """
        Raise a [textDocument/documentSymbol](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_documentSymbol) request to the Language Server
        to find symbols in the given file. Wait for the response and return the result.

        :param relative_file_path: The relative path of the file that has the symbols

        :return Tuple[List[multilspy_types.UnifiedSymbolInformation], Union[List[multilspy_types.TreeRepr], None]]: A list of symbols in the file, and the tree representation of the symbols
        """
        with self.file_opened(relative_file_path):
            response = await self.server.send.document_symbol(
                LSPTypes.DocumentSymbolParams.model_validate(
                    {
                        "textDocument": {
                            "uri": pathlib.Path(
                                os.path.join(
                                    self.repository_root_path, relative_file_path
                                )
                            ).as_uri()
                        }
                    }
                )
            )

        ret: List[multilspy_types.UnifiedSymbolInformation] = []
        l_tree = None
        assert response is not None
        for item in response:

            if isinstance(item, LSPTypes.DocumentSymbol) and item.children:
                # TODO: l_tree should be a list of TreeRepr. Define the following function to return TreeRepr as well

                def visit_tree_nodes_and_build_tree_repr(
                    tree: LSPTypes.DocumentSymbol,
                ) -> List[multilspy_types.UnifiedSymbolInformation]:
                    l: List[multilspy_types.UnifiedSymbolInformation] = []
                    children = tree.children if tree.children else []
                    if tree.children:
                        tree.children = None

                    l.append(
                        multilspy_types.UnifiedSymbolInformation.model_validate(tree)
                    )
                    for child in children:
                        l.extend(visit_tree_nodes_and_build_tree_repr(child))
                    return l

                ret.extend(visit_tree_nodes_and_build_tree_repr(item))
            else:
                ret.append(
                    multilspy_types.UnifiedSymbolInformation.model_validate(item)
                )

        return ret, l_tree

    async def request_hover(
        self, relative_file_path: str, line: int, column: int
    ) -> Union[multilspy_types.Hover, None]:
        """
        Raise a [textDocument/hover](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_hover) request to the Language Server
        to find the hover information at the given line and column in the given file. Wait for the response and return the result.

        :param relative_file_path: The relative path of the file that has the hover information
        :param line: The line number of the symbol
        :param column: The column number of the symbol

        :return None
        """
        with self.file_opened(relative_file_path):
            response = await self.server.send.hover(
                LSPTypes.HoverParams.model_validate(
                    {
                        "textDocument": {
                            "uri": pathlib.Path(
                                os.path.join(
                                    self.repository_root_path, relative_file_path
                                )
                            ).as_uri()
                        },
                        "position": {
                            "line": line,
                            "character": column,
                        },
                    }
                )
            )

        return multilspy_types.Hover.model_validate(response) if response else None


@ensure_all_methods_implemented(LanguageServer)
class SyncLanguageServer:
    """
    The SyncLanguageServer class provides a language agnostic interface to the Language Server Protocol.
    It is used to communicate with Language Servers of different programming languages.
    """

    def __init__(self, language_server: LanguageServer) -> None:
        self.language_server = language_server
        # self.loop = None
        # self.loop_thread = None

    @classmethod
    def create(
        cls,
        config: MultilspyConfig,
        repository_root_path: str,
        logger: Optional[logging.Logger] = None,
    ) -> "SyncLanguageServer":
        """
        Creates a language specific LanguageServer instance based on the given configuration, and appropriate settings for the programming language.

        If language is Java, then ensure that jdk-17.0.6 or higher is installed, `java` is in PATH, and JAVA_HOME is set to the installation directory.

        :param repository_root_path: The root path of the repository.
        :param config: The Multilspy configuration.
        :param logger: The logger to use.

        :return SyncLanguageServer: A language specific LanguageServer instance.
        """
        return SyncLanguageServer(
            LanguageServer.create(config, repository_root_path, logger)
        )

    @contextmanager
    def file_opened(self, relative_file_path: str) -> Iterator[None]:
        """
        Open a file in the Language Server. This is required before making any requests to the Language Server.

        :param relative_file_path: The relative path of the file to open.
        """
        with self.language_server.file_opened(relative_file_path):
            yield

    def insert_text_at_position(
        self, relative_file_path: str, line: int, column: int, text_to_be_inserted: str
    ) -> multilspy_types.Position:
        """
        Insert text at the given line and column in the given file and return
        the updated cursor position after inserting the text.

        :param relative_file_path: The relative path of the file to open.
        :param line: The line number at which text should be inserted.
        :param column: The column number at which text should be inserted.
        :param text_to_be_inserted: The text to insert.
        """
        return self.language_server.insert_text_at_position(
            relative_file_path, line, column, text_to_be_inserted
        )

    def delete_text_between_positions(
        self,
        relative_file_path: str,
        start: multilspy_types.Position,
        end: multilspy_types.Position,
    ) -> str:
        """
        Delete text between the given start and end positions in the given file and return the deleted text.
        """
        return self.language_server.delete_text_between_positions(
            relative_file_path, start, end
        )

    def get_open_file_text(self, relative_file_path: str) -> str:
        """
        Get the contents of the given opened file as per the Language Server.

        :param relative_file_path: The relative path of the file to open.
        """
        return self.language_server.get_open_file_text(relative_file_path)

    def start(self):
        self.loop = asyncio.new_event_loop()
        self.loop_thread = threading.Thread(target=self.loop.run_forever, daemon=True)
        self.loop_thread.start()
        asyncio.run_coroutine_threadsafe(
            self.language_server.start(), loop=self.loop
        ).result()

    def stop(self):
        if self.loop is None or self.loop_thread is None:
            raise MultilspyException("Language Server not started")
        asyncio.run_coroutine_threadsafe(
            self.language_server.stop(), loop=self.loop
        ).result()
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.loop_thread.join()

    @contextmanager
    def running(self) -> Iterator["SyncLanguageServer"]:
        """
        Starts the language server process and connects to it.

        :return: None
        """
        self.start()
        try:
            yield self
        finally:
            self.stop()

    def request_definition(
        self, file_path: str, line: int, column: int
    ) -> List[multilspy_types.Location]:
        """
        Raise a [textDocument/definition](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_definition) request to the Language Server
        for the symbol at the given line and column in the given file. Wait for the response and return the result.

        :param relative_file_path: The relative path of the file that has the symbol for which definition should be looked up
        :param line: The line number of the symbol
        :param column: The column number of the symbol

        :return List[multilspy_types.Location]: A list of locations where the symbol is defined
        """
        result = asyncio.run_coroutine_threadsafe(
            self.language_server.request_definition(file_path, line, column), self.loop
        ).result()
        return result

    def request_references(
        self, file_path: str, line: int, column: int
    ) -> List[multilspy_types.Location]:
        """
        Raise a [textDocument/references](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_references) request to the Language Server
        to find references to the symbol at the given line and column in the given file. Wait for the response and return the result.

        :param relative_file_path: The relative path of the file that has the symbol for which references should be looked up
        :param line: The line number of the symbol
        :param column: The column number of the symbol

        :return List[multilspy_types.Location]: A list of locations where the symbol is referenced
        """
        result = asyncio.run_coroutine_threadsafe(
            self.language_server.request_references(file_path, line, column), self.loop
        ).result()
        return result

    def request_completions(
        self,
        relative_file_path: str,
        line: int,
        column: int,
        allow_incomplete: bool = False,
    ) -> List[multilspy_types.CompletionItem]:
        """
        Raise a [textDocument/completion](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_completion) request to the Language Server
        to find completions at the given line and column in the given file. Wait for the response and return the result.

        :param relative_file_path: The relative path of the file that has the symbol for which completions should be looked up
        :param line: The line number of the symbol
        :param column: The column number of the symbol

        :return List[multilspy_types.CompletionItem]: A list of completions
        """
        result = asyncio.run_coroutine_threadsafe(
            self.language_server.request_completions(
                relative_file_path, line, column, allow_incomplete
            ),
            self.loop,
        ).result()
        return result

    def request_document_symbols(self, relative_file_path: str) -> Tuple[
        List[multilspy_types.UnifiedSymbolInformation],
        Union[List[multilspy_types.TreeRepr], None],
    ]:
        """
        Raise a [textDocument/documentSymbol](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_documentSymbol) request to the Language Server
        to find symbols in the given file. Wait for the response and return the result.

        :param relative_file_path: The relative path of the file that has the symbols

        :return Tuple[List[multilspy_types.UnifiedSymbolInformation], Union[List[multilspy_types.TreeRepr], None]]: A list of symbols in the file, and the tree representation of the symbols
        """
        result = asyncio.run_coroutine_threadsafe(
            self.language_server.request_document_symbols(relative_file_path), self.loop
        ).result()
        return result

    def request_hover(
        self, relative_file_path: str, line: int, column: int
    ) -> Union[multilspy_types.Hover, None]:
        """
        Raise a [textDocument/hover](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_hover) request to the Language Server
        to find the hover information at the given line and column in the given file. Wait for the response and return the result.

        :param relative_file_path: The relative path of the file that has the hover information
        :param line: The line number of the symbol
        :param column: The column number of the symbol

        :return None
        """
        result = asyncio.run_coroutine_threadsafe(
            self.language_server.request_hover(relative_file_path, line, column),
            self.loop,
        ).result()
        return result
