"""
Provides Rust specific instantiation of the LanguageServer class. Contains various configurations and settings specific to Rust.
"""

import asyncio
import json
import logging
import os
import pathlib
import stat

from multilspy.language_server import LanguageServer
from multilspy.lsp_protocol_handler.lsp_types import (
    CompletionOptions,
    InitializedParams,
    InitializeParams,
    InitializeResult,
    TextDocumentSyncKind,
    TextDocumentSyncOptions,
)
from multilspy.lsp_protocol_handler.server import ProcessLaunchInfo
from multilspy.multilspy_config import MultilspyConfig
from multilspy.multilspy_utils import FileUtils, PlatformUtils


class RustAnalyzer(LanguageServer):
    """
    Provides Rust specific instantiation of the LanguageServer class. Contains various configurations and settings specific to Rust.
    """

    def __init__(
        self,
        config: MultilspyConfig,
        logger: logging.Logger,
        repository_root_path: str,
    ):
        """
        Creates a RustAnalyzer instance. This class is not meant to be instantiated directly. Use LanguageServer.create() instead.
        """
        rustanalyzer_executable_path = self.setup_runtime_dependencies(logger, config)
        super().__init__(
            config,
            logger,
            repository_root_path,
            ProcessLaunchInfo(
                cmd=rustanalyzer_executable_path, cwd=repository_root_path
            ),
            "rust",
        )
        self.server_ready = asyncio.Event()

    def setup_runtime_dependencies(
        self, logger: logging.Logger, config: MultilspyConfig
    ) -> str:
        """
        Setup runtime dependencies for rust_analyzer.
        """
        platform_id = PlatformUtils.get_platform_id()

        with open(
            os.path.join(os.path.dirname(__file__), "runtime_dependencies.json"), "r"
        ) as f:
            d = json.load(f)
            del d["_description"]

        # assert platform_id.value in [
        #     "linux-x64",
        #     "win-x64",
        # ], "Only linux-x64 and win-x64 platform is supported for in multilspy at the moment"

        runtime_dependencies = d["runtimeDependencies"]
        runtime_dependencies = [
            dependency
            for dependency in runtime_dependencies
            if dependency["platformId"] == platform_id.value
        ]
        assert len(runtime_dependencies) == 1
        dependency = runtime_dependencies[0]

        rustanalyzer_ls_dir = os.path.join(
            os.path.dirname(__file__), "static", "RustAnalyzer"
        )
        rustanalyzer_executable_path = os.path.join(
            rustanalyzer_ls_dir, dependency["binaryName"]
        )
        if not os.path.exists(rustanalyzer_ls_dir):
            os.makedirs(rustanalyzer_ls_dir)
            if dependency["archiveType"] == "gz":
                FileUtils.download_and_extract_archive(
                    dependency["url"],
                    rustanalyzer_executable_path,
                    dependency["archiveType"],
                    logger,
                )
            else:
                FileUtils.download_and_extract_archive(
                    dependency["url"],
                    rustanalyzer_ls_dir,
                    dependency["archiveType"],
                    logger,
                )
        assert os.path.exists(rustanalyzer_executable_path)
        os.chmod(rustanalyzer_executable_path, stat.S_IEXEC)

        return rustanalyzer_executable_path

    def _get_initialize_params(self, repository_absolute_path: str) -> InitializeParams:
        """
        Returns the initialize params for the Rust Analyzer Language Server.
        """
        with open(
            os.path.join(os.path.dirname(__file__), "initialize_params.json"), "r"
        ) as f:
            d = json.load(f)

        del d["_description"]

        d["processId"] = os.getpid()
        assert d["rootPath"] == "$rootPath"
        d["rootPath"] = repository_absolute_path

        assert d["rootUri"] == "$rootUri"
        d["rootUri"] = pathlib.Path(repository_absolute_path).as_uri()

        assert d["workspaceFolders"][0]["uri"] == "$uri"
        d["workspaceFolders"][0]["uri"] = pathlib.Path(
            repository_absolute_path
        ).as_uri()

        assert d["workspaceFolders"][0]["name"] == "$name"
        d["workspaceFolders"][0]["name"] = os.path.basename(repository_absolute_path)

        return InitializeParams.model_validate(d)

    async def start(self):

        async def execute_client_command_handler(params):
            return []

        async def do_nothing(params):
            return

        async def check_experimental_status(params):
            if params["quiescent"] == True:
                self.server_ready.set()

        async def window_log_message(msg):
            self.logger.error(f"LSP: window/logMessage: {msg}")

        self.server.on_request("client/registerCapability", do_nothing)
        self.server.on_notification("language/status", do_nothing)
        self.server.on_notification("window/logMessage", window_log_message)
        self.server.on_request(
            "workspace/executeClientCommand", execute_client_command_handler
        )
        self.server.on_notification("$/progress", do_nothing)
        self.server.on_notification("textDocument/publishDiagnostics", do_nothing)
        self.server.on_notification("language/actionableNotification", do_nothing)
        self.server.on_notification(
            "experimental/serverStatus", check_experimental_status
        )
        self.logger.info("Starting RustAnalyzer server process")
        await self.server.start()
        initialize_params = self._get_initialize_params(self.repository_root_path)
        self.logger.info(
            "Sending initialize request from LSP client to LSP server and awaiting response"
        )
        init_response: InitializeResult = await self.server.send.initialize(
            initialize_params
        )
        assert (
            isinstance(
                init_response.capabilities.textDocumentSync, TextDocumentSyncOptions
            )
            and init_response.capabilities.textDocumentSync.change
            == TextDocumentSyncKind.Incremental
        )
        assert init_response.capabilities.completionProvider
        assert (
            init_response.capabilities.completionProvider
            == CompletionOptions.model_validate(
                {
                    "resolveProvider": True,
                    "triggerCharacters": [":", ".", "'", "("],
                    "completionItem": {"labelDetailsSupport": True},
                }
            )
        )
        self.server.notify.initialized(InitializedParams())
        self.completions_available.set()

        await self.server_ready.wait()
        await super().start()
