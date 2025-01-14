# Code generated. DO NOT EDIT.
# LSP v3.17.0
# TODO: Look into use of https://pypi.org/project/ts2python/ to generate the types for https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/

"""
This file provides the python interface corresponding to the requests and notifications defined in Typescript in the language server protocol.
This file is obtained from https://github.com/predragnikolic/OLSP under the MIT License with the following terms:

MIT License

Copyright (c) 2023 Предраг Николић

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from typing import Awaitable, Callable, List, Optional, TypeVar, Union

from pydantic import TypeAdapter

from multilspy.lsp_protocol_handler import lsp_types

from .lsp_types import LSPAny, Params

T = TypeVar("T", bound=Params)
R = TypeVar("R")


def implement_send(method: str):
    def decorator(func: Callable[["LspRequest", T], Awaitable[R]]):
        ret_type = func.__annotations__.get("return")
        type_adapter = TypeAdapter(ret_type)

        async def wrapper(self: "LspRequest", params: Params) -> R:
            res = await self.send_request(method, params)
            return type_adapter.validate_python(res)

        return wrapper

    return decorator


def implement_notify(method: str):
    def decorator(func: Callable[["LspNotification", T], None]):
        def wrapper(self: "LspNotification", params: Params) -> None:
            self.send_notification(method, params)

        return wrapper

    return decorator


class LspRequest:
    def __init__(
        self,
        send_request: Callable[[str, Optional[Params]], Awaitable[Optional[LSPAny]]],
    ):
        self.send_request = send_request
        self._implementation_adapter = TypeAdapter(
            Optional[lsp_types.Definition | List[lsp_types.LocationLink]]
        )
        self._type_defintion_adapter = TypeAdapter(
            Optional[lsp_types.Definition | List[lsp_types.LocationLink]]
        )

    @implement_send("textDocument/implementation")
    async def implementation(
        self, params: lsp_types.ImplementationParams
    ) -> Optional[lsp_types.Definition | List[lsp_types.LocationLink]]:
        """A request to resolve the implementation locations of a symbol at a given text
        document position. The request's parameter is of type [TextDocumentPositionParams]
        (#TextDocumentPositionParams) the response is of type {@link Definition} or a
        Thenable that resolves to such."""
        pass

    @implement_send("textDocument/typeDefinition")
    async def type_definition(
        self, params: lsp_types.TypeDefinitionParams
    ) -> Optional[lsp_types.Definition | List[lsp_types.LocationLink]]:
        """A request to resolve the type definition locations of a symbol at a given text
        document position. The request's parameter is of type [TextDocumentPositionParams]
        (#TextDocumentPositionParams) the response is of type {@link Definition} or a
        Thenable that resolves to such."""
        pass

    @implement_send("textDocument/documentColor")
    async def document_color(
        self, params: lsp_types.DocumentColorParams
    ) -> List[lsp_types.ColorInformation]:  # type:ignore
        """A request to list all color symbols found in a given text document. The request's
        parameter is of type {@link DocumentColorParams} the
        response is of type {@link ColorInformation ColorInformation[]} or a Thenable
        that resolves to such."""
        pass

    @implement_send("textDocument/colorPresentation")
    async def color_presentation(
        self, params: lsp_types.ColorPresentationParams
    ) -> List[lsp_types.ColorPresentation]:  # type:ignore
        """A request to list all presentation for a color. The request's
        parameter is of type {@link ColorPresentationParams} the
        response is of type {@link ColorInformation ColorInformation[]} or a Thenable
        that resolves to such."""
        pass

    @implement_send("textDocument/foldingRange")
    async def folding_range(
        self, params: lsp_types.FoldingRangeParams
    ) -> Optional[List[lsp_types.FoldingRange]]:
        """A request to provide folding ranges in a document. The request's
        parameter is of type {@link FoldingRangeParams}, the
        response is of type {@link FoldingRangeList} or a Thenable
        that resolves to such."""
        pass

    @implement_send("textDocument/declaration")
    async def declaration(
        self, params: lsp_types.DeclarationParams
    ) -> Optional[lsp_types.Declaration | List[lsp_types.LocationLink]]:
        """A request to resolve the type definition locations of a symbol at a given text
        document position. The request's parameter is of type [TextDocumentPositionParams]
        (#TextDocumentPositionParams) the response is of type {@link Declaration}
        or a typed array of {@link DeclarationLink} or a Thenable that resolves
        to such."""
        pass

    @implement_send("textDocument/selectionRange")
    async def selection_range(
        self, params: lsp_types.SelectionRangeParams
    ) -> Optional[List[lsp_types.SelectionRange]]:
        """A request to provide selection ranges in a document. The request's
        parameter is of type {@link SelectionRangeParams}, the
        response is of type {@link SelectionRange SelectionRange[]} or a Thenable
        that resolves to such."""
        pass

    @implement_send("textDocument/prepareCallHierarchy")
    async def prepare_call_hierarchy(
        self, params: lsp_types.CallHierarchyPrepareParams
    ) -> Optional[List[lsp_types.CallHierarchyItem]]:
        """A request to result a `CallHierarchyItem` in a document at a given position.
        Can be used as an input to an incoming or outgoing call hierarchy.

        @since 3.16.0"""
        pass

    @implement_send("callHierarchy/incomingCalls")
    async def incoming_calls(
        self, params: lsp_types.CallHierarchyIncomingCallsParams
    ) -> Optional[List[lsp_types.CallHierarchyIncomingCall]]:
        """A request to resolve the incoming calls for a given `CallHierarchyItem`.

        @since 3.16.0"""
        pass

    @implement_send("callHierarchy/outgoingCalls")
    async def outgoing_calls(
        self, params: lsp_types.CallHierarchyOutgoingCallsParams
    ) -> Optional[List[lsp_types.CallHierarchyOutgoingCall]]:
        """A request to resolve the outgoing calls for a given `CallHierarchyItem`.

        @since 3.16.0"""
        pass

    @implement_send("textDocument/semanticTokens/full")
    async def semantic_tokens_full(
        self, params: lsp_types.SemanticTokensParams
    ) -> Optional[lsp_types.SemanticTokens]:
        """@since 3.16.0"""
        pass

    @implement_send("textDocument/semanticTokens/full/delta")
    async def semantic_tokens_delta(
        self, params: lsp_types.SemanticTokensDeltaParams
    ) -> Optional[lsp_types.SemanticTokens | lsp_types.SemanticTokensDelta]:
        """@since 3.16.0"""
        pass

    @implement_send("textDocument/semanticTokens/range")
    async def semantic_tokens_range(
        self, params: lsp_types.SemanticTokensRangeParams
    ) -> Optional[lsp_types.SemanticTokens]:
        """@since 3.16.0"""
        pass

    @implement_send("textDocument/linkedEditingRange")
    async def linked_editing_range(
        self, params: lsp_types.LinkedEditingRangeParams
    ) -> Optional[lsp_types.LinkedEditingRanges]:
        """A request to provide ranges that can be edited together.

        @since 3.16.0"""
        pass

    @implement_send("workspace/willCreateFiles")
    async def will_create_files(
        self, params: lsp_types.CreateFilesParams
    ) -> Optional[lsp_types.WorkspaceEdit]:
        """The will create files request is sent from the client to the server before files are actually
        created as long as the creation is triggered from within the client.

        @since 3.16.0"""
        pass

    @implement_send("workspace/willRenameFiles")
    async def will_rename_files(
        self, params: lsp_types.RenameFilesParams
    ) -> Optional[lsp_types.WorkspaceEdit]:
        """The will rename files request is sent from the client to the server before files are actually
        renamed as long as the rename is triggered from within the client.

        @since 3.16.0"""
        pass

    @implement_send("workspace/willDeleteFiles")
    async def will_delete_files(
        self, params: lsp_types.DeleteFilesParams
    ) -> Optional[lsp_types.WorkspaceEdit]:
        """The did delete files notification is sent from the client to the server when
        files were deleted from within the client.

        @since 3.16.0"""
        pass

    @implement_send("textDocument/moniker")
    async def moniker(
        self, params: lsp_types.MonikerParams
    ) -> Optional[List[lsp_types.Moniker]]:
        """A request to get the moniker of a symbol at a given text document position.
        The request parameter is of type {@link TextDocumentPositionParams}.
        The response is of type {@link Moniker Moniker[]} or `null`."""
        pass

    @implement_send("textDocument/prepareTypeHierarchy")
    async def prepare_type_hierarchy(
        self, params: lsp_types.TypeHierarchyPrepareParams
    ) -> Optional[List[lsp_types.TypeHierarchyItem]]:
        """A request to result a `TypeHierarchyItem` in a document at a given position.
        Can be used as an input to a subtypes or supertypes type hierarchy.

        @since 3.17.0"""
        pass

    @implement_send("typeHierarchy/supertypes")
    async def type_hierarchy_supertypes(
        self, params: lsp_types.TypeHierarchySupertypesParams
    ) -> Optional[List[lsp_types.TypeHierarchyItem]]:
        """A request to resolve the supertypes for a given `TypeHierarchyItem`.

        @since 3.17.0"""
        pass

    @implement_send("typeHierarchy/subtypes")
    async def type_hierarchy_subtypes(
        self, params: lsp_types.TypeHierarchySubtypesParams
    ) -> Optional[List[lsp_types.TypeHierarchyItem]]:
        """A request to resolve the subtypes for a given `TypeHierarchyItem`.

        @since 3.17.0"""
        pass

    @implement_send("textDocument/inlineValue")
    async def inline_value(
        self, params: lsp_types.InlineValueParams
    ) -> Optional[List[lsp_types.InlineValue]]:
        """A request to provide inline values in a document. The request's parameter is of
        type {@link InlineValueParams}, the response is of type
        {@link InlineValue InlineValue[]} or a Thenable that resolves to such.

        @since 3.17.0"""
        pass

    @implement_send("textDocument/inlayHint")
    async def inlay_hint(
        self, params: lsp_types.InlayHintParams
    ) -> Optional[List[lsp_types.InlayHint]]:
        """A request to provide inlay hints in a document. The request's parameter is of
        type {@link InlayHintsParams}, the response is of type
        {@link InlayHint InlayHint[]} or a Thenable that resolves to such.

        @since 3.17.0"""
        pass

    @implement_send("inlayHint/resolve")
    async def resolve_inlay_hint(
        self, params: lsp_types.InlayHint
    ) -> lsp_types.InlayHint:  # type:ignore
        """A request to resolve additional properties for an inlay hint.
        The request's parameter is of type {@link InlayHint}, the response is
        of type {@link InlayHint} or a Thenable that resolves to such.

        @since 3.17.0"""
        pass

    @implement_send("textDocument/diagnostic")
    async def text_document_diagnostic(
        self, params: lsp_types.DocumentDiagnosticParams
    ) -> lsp_types.DocumentDiagnosticReport:  # type:ignore
        """The document diagnostic request definition.

        @since 3.17.0"""
        pass

    @implement_send("workspace/diagnostic")
    async def workspace_diagnostic(
        self, params: lsp_types.WorkspaceDiagnosticParams
    ) -> lsp_types.WorkspaceDiagnosticReport:  # type:ignore
        """The workspace diagnostic request definition.

        @since 3.17.0"""
        pass

    @implement_send("initialize")
    async def initialize(
        self, params: lsp_types.InitializeParams
    ) -> lsp_types.InitializeResult:  # type:ignore
        """The initialize request is sent from the client to the server.
        It is sent once as the request after starting up the server.
        The requests parameter is of type {@link InitializeParams}
        the response if of type {@link InitializeResult} of a Thenable that
        resolves to such."""
        pass

    async def shutdown(self) -> None:
        """A shutdown request is sent from the client to the server.
        It is sent once when the client decides to shutdown the
        server. The only notification that is sent after a shutdown request
        is the exit event."""
        await self.send_request("shutdown", None)

    @implement_send("textDocument/willSaveWaitUntil")
    async def will_save_wait_until(
        self, params: lsp_types.WillSaveTextDocumentParams
    ) -> Optional[List[lsp_types.TextEdit]]:
        """A document will save request is sent from the client to the server before
        the document is actually saved. The request can return an array of TextEdits
        which will be applied to the text document before it is saved. Please note that
        clients might drop results if computing the text edits took too long or if a
        server constantly fails on this request. This is done to keep the save fast and
        reliable."""
        pass

    @implement_send("textDocument/completion")
    async def completion(
        self, params: lsp_types.CompletionParams
    ) -> Optional[List[lsp_types.CompletionItem] | lsp_types.CompletionList]:
        """Request to request completion at a given text document position. The request's
        parameter is of type {@link TextDocumentPosition} the response
        is of type {@link CompletionItem CompletionItem[]} or {@link CompletionList}
        or a Thenable that resolves to such.

        The request can delay the computation of the {@link CompletionItem.detail `detail`}
        and {@link CompletionItem.documentation `documentation`} properties to the `completionItem/resolve`
        request. However, properties that are needed for the initial sorting and filtering, like `sortText`,
        `filterText`, `insertText`, and `textEdit`, must not be changed during resolve.
        """
        pass

    @implement_send("completionItem/resolve")
    async def resolve_completion_item(
        self, params: lsp_types.CompletionItem
    ) -> lsp_types.CompletionItem:  # type:ignore
        """Request to resolve additional information for a given completion item.The request's
        parameter is of type {@link CompletionItem} the response
        is of type {@link CompletionItem} or a Thenable that resolves to such."""
        pass

    @implement_send("textDocument/hover")
    async def hover(self, params: lsp_types.HoverParams) -> Optional[lsp_types.Hover]:
        """Request to request hover information at a given text document position. The request's
        parameter is of type {@link TextDocumentPosition} the response is of
        type {@link Hover} or a Thenable that resolves to such."""
        pass

    @implement_send("textDocument/signatureHelp")
    async def signature_help(
        self, params: lsp_types.SignatureHelpParams
    ) -> Optional[lsp_types.SignatureHelp]:
        pass

    @implement_send("textDocument/definition")
    async def definition(
        self, params: lsp_types.DefinitionParams
    ) -> Optional[lsp_types.Definition | List[lsp_types.LocationLink]]:
        """A request to resolve the definition location of a symbol at a given text
        document position. The request's parameter is of type [TextDocumentPosition]
        (#TextDocumentPosition) the response is of either type {@link Definition}
        or a typed array of {@link DefinitionLink} or a Thenable that resolves
        to such."""
        pass

    @implement_send("textDocument/references")
    async def references(
        self, params: lsp_types.ReferenceParams
    ) -> Optional[List[lsp_types.Location]]:
        """A request to resolve project-wide references for the symbol denoted
        by the given text document position. The request's parameter is of
        type {@link ReferenceParams} the response is of type
        {@link Location Location[]} or a Thenable that resolves to such."""
        pass

    @implement_send("textDocument/documentHighlight")
    async def document_highlight(
        self, params: lsp_types.DocumentHighlightParams
    ) -> Optional[List[lsp_types.DocumentHighlight]]:
        """Request to resolve a {@link DocumentHighlight} for a given
        text document position. The request's parameter is of type [TextDocumentPosition]
        (#TextDocumentPosition) the request response is of type [DocumentHighlight[]]
        (#DocumentHighlight) or a Thenable that resolves to such."""
        pass

    @implement_send("textDocument/documentSymbol")
    async def document_symbol(
        self, params: lsp_types.DocumentSymbolParams
    ) -> Optional[List[lsp_types.SymbolInformation] | List[lsp_types.DocumentSymbol]]:
        """A request to list all symbols found in a given text document. The request's
        parameter is of type {@link TextDocumentIdentifier} the
        response is of type {@link SymbolInformation SymbolInformation[]} or a Thenable
        that resolves to such."""
        pass

    @implement_send("textDocument/codeAction")
    async def code_action(
        self, params: lsp_types.CodeActionParams
    ) -> Optional[List[Union[lsp_types.Command, lsp_types.CodeAction]]]:
        """A request to provide commands for the given text document and range."""
        pass

    @implement_send("codeAction/resolve")
    async def resolve_code_action(
        self, params: lsp_types.CodeAction
    ) -> lsp_types.CodeAction:  # type:ignore
        """Request to resolve additional information for a given code action.The request's
        parameter is of type {@link CodeAction} the response
        is of type {@link CodeAction} or a Thenable that resolves to such."""
        pass

    @implement_send("workspace/symbol")
    async def workspace_symbol(
        self, params: lsp_types.WorkspaceSymbolParams
    ) -> Union[
        List[lsp_types.SymbolInformation], List[lsp_types.WorkspaceSymbol], None
    ]:
        """A request to list project-wide symbols matching the query string given
        by the {@link WorkspaceSymbolParams}. The response is
        of type {@link SymbolInformation SymbolInformation[]} or a Thenable that
        resolves to such.

        @since 3.17.0 - support for WorkspaceSymbol in the returned data. Clients
         need to advertise support for WorkspaceSymbols via the client capability
         `workspace.symbol.resolveSupport`.
        """
        pass

    @implement_send("workspaceSymbol/resolve")
    async def resolve_workspace_symbol(
        self, params: lsp_types.WorkspaceSymbol
    ) -> lsp_types.WorkspaceSymbol:  # type:ignore
        """A request to resolve the range inside the workspace
        symbol's location.

        @since 3.17.0"""
        pass

    @implement_send("textDocument/codeLens")
    async def code_lens(
        self, params: lsp_types.CodeLensParams
    ) -> Optional[List[lsp_types.CodeLens]]:
        """A request to provide code lens for the given text document."""
        pass

    @implement_send("codeLens/resolve")
    async def resolve_code_lens(
        self, params: lsp_types.CodeLens
    ) -> lsp_types.CodeLens:  # type:ignore
        """A request to resolve a command for a given code lens."""
        pass

    @implement_send("textDocument/documentLink")
    async def document_link(
        self, params: lsp_types.DocumentLinkParams
    ) -> Optional[List[lsp_types.DocumentLink]]:
        """A request to provide document links"""
        pass

    @implement_send("documentLink/resolve")
    async def resolve_document_link(
        self, params: lsp_types.DocumentLink
    ) -> lsp_types.DocumentLink:  # type:ignore
        """Request to resolve additional information for a given document link. The request's
        parameter is of type {@link DocumentLink} the response
        is of type {@link DocumentLink} or a Thenable that resolves to such."""
        pass

    @implement_send("textDocument/formatting")
    async def formatting(
        self, params: lsp_types.DocumentFormattingParams
    ) -> Optional[List[lsp_types.TextEdit]]:
        """A request to to format a whole document."""
        pass

    @implement_send("textDocument/rangeFormatting")
    async def range_formatting(
        self, params: lsp_types.DocumentRangeFormattingParams
    ) -> Optional[List[lsp_types.TextEdit]]:
        """A request to to format a range in a document."""
        pass

    @implement_send("textDocument/onTypeFormatting")
    async def on_type_formatting(
        self, params: lsp_types.DocumentOnTypeFormattingParams
    ) -> Optional[List[lsp_types.TextEdit]]:
        """A request to format a document on type."""
        pass

    @implement_send("textDocument/rename")
    async def rename(
        self, params: lsp_types.RenameParams
    ) -> Optional[lsp_types.WorkspaceEdit]:
        """A request to rename a symbol."""
        pass

    @implement_send("textDocument/prepareRename")
    async def prepare_rename(
        self, params: lsp_types.PrepareRenameParams
    ) -> Optional[lsp_types.PrepareRenameResult]:
        """A request to test and perform the setup necessary for a rename.

        @since 3.16 - support for default behavior"""
        pass

    @implement_send("workspace/executeCommand")
    async def execute_command(
        self, params: lsp_types.ExecuteCommandParams
    ) -> Optional[lsp_types.LSPAny]:
        """A request send from the client to the server to execute a command. The request might return
        a workspace edit which the client will apply to the workspace."""
        pass


class LspNotification:
    def __init__(self, send_notification: Callable[[str, Optional[Params]], None]):
        self.send_notification = send_notification

    @implement_notify("workspace/didChangeWorkspaceFolders")
    def did_change_workspace_folders(
        self, params: lsp_types.DidChangeWorkspaceFoldersParams
    ) -> None:
        """The `workspace/didChangeWorkspaceFolders` notification is sent from the client to the server when the workspace
        folder configuration changes."""
        pass

    @implement_notify("window/workDoneProgress/cancel")
    def cancel_work_done_progress(
        self, params: lsp_types.WorkDoneProgressCancelParams
    ) -> None:
        """The `window/workDoneProgress/cancel` notification is sent from  the client to the server to cancel a progress
        initiated on the server side."""
        pass

    @implement_notify("workspace/didCreateFiles")
    def did_create_files(self, params: lsp_types.CreateFilesParams) -> None:
        """The did create files notification is sent from the client to the server when
        files were created from within the client.

        @since 3.16.0"""
        pass

    @implement_notify("workspace/didRenameFiles")
    def did_rename_files(self, params: lsp_types.RenameFilesParams) -> None:
        """The did rename files notification is sent from the client to the server when
        files were renamed from within the client.

        @since 3.16.0"""
        pass

    @implement_notify("workspace/didDeleteFiles")
    def did_delete_files(self, params: lsp_types.DeleteFilesParams) -> None:
        """The will delete files request is sent from the client to the server before files are actually
        deleted as long as the deletion is triggered from within the client.

        @since 3.16.0"""
        pass

    @implement_notify("notebookDocument/didOpen")
    def did_open_notebook_document(
        self, params: lsp_types.DidOpenNotebookDocumentParams
    ) -> None:
        """A notification sent when a notebook opens.

        @since 3.17.0"""
        pass

    @implement_notify("notebookDocument/didChange")
    def did_change_notebook_document(
        self, params: lsp_types.DidChangeNotebookDocumentParams
    ) -> None:
        pass

    @implement_notify("notebookDocument/didSave")
    def did_save_notebook_document(
        self, params: lsp_types.DidSaveNotebookDocumentParams
    ) -> None:
        """A notification sent when a notebook document is saved.

        @since 3.17.0"""
        pass

    @implement_notify("notebookDocument/didClose")
    def did_close_notebook_document(
        self, params: lsp_types.DidCloseNotebookDocumentParams
    ) -> None:
        """A notification sent when a notebook closes.

        @since 3.17.0"""
        pass

    @implement_notify("initialized")
    def initialized(self, params: lsp_types.InitializedParams) -> None:
        """The initialized notification is sent from the client to the
        server after the client is fully initialized and the server
        is allowed to send requests from the server to the client."""
        pass

    def exit(self) -> None:
        """The exit event is sent from the client to the server to
        ask the server to exit its process."""
        return self.send_notification("exit", None)

    @implement_notify("workspace/didChangeConfiguration")
    def workspace_did_change_configuration(
        self, params: lsp_types.DidChangeConfigurationParams
    ) -> None:
        """The configuration change notification is sent from the client to the server
        when the client's configuration has changed. The notification contains
        the changed configuration as defined by the language client."""
        pass

    @implement_notify("textDocument/didOpen")
    def did_open_text_document(
        self, params: lsp_types.DidOpenTextDocumentParams
    ) -> None:
        """The document open notification is sent from the client to the server to signal
        newly opened text documents. The document's truth is now managed by the client
        and the server must not try to read the document's truth using the document's
        uri. Open in this sense means it is managed by the client. It doesn't necessarily
        mean that its content is presented in an editor. An open notification must not
        be sent more than once without a corresponding close notification send before.
        This means open and close notification must be balanced and the max open count
        is one."""
        pass

    @implement_notify("textDocument/didChange")
    def did_change_text_document(
        self, params: lsp_types.DidChangeTextDocumentParams
    ) -> None:
        """The document change notification is sent from the client to the server to signal
        changes to a text document."""
        pass

    @implement_notify("textDocument/didClose")
    def did_close_text_document(
        self, params: lsp_types.DidCloseTextDocumentParams
    ) -> None:
        """The document close notification is sent from the client to the server when
        the document got closed in the client. The document's truth now exists where
        the document's uri points to (e.g. if the document's uri is a file uri the
        truth now exists on disk). As with the open notification the close notification
        is about managing the document's content. Receiving a close notification
        doesn't mean that the document was open in an editor before. A close
        notification requires a previous open notification to be sent."""
        pass

    @implement_notify("textDocument/didSave")
    def did_save_text_document(
        self, params: lsp_types.DidSaveTextDocumentParams
    ) -> None:
        """The document save notification is sent from the client to the server when
        the document got saved in the client."""
        pass

    @implement_notify("textDocument/willSave")
    def will_save_text_document(
        self, params: lsp_types.WillSaveTextDocumentParams
    ) -> None:
        """A document will save notification is sent from the client to the server before
        the document is actually saved."""
        pass

    @implement_notify("workspace/didChangeWatchedFiles")
    def did_change_watched_files(
        self, params: lsp_types.DidChangeWatchedFilesParams
    ) -> None:
        """The watched files notification is sent from the client to the server when
        the client detects changes to file watched by the language client."""
        pass

    @implement_notify("$/setTrace")
    def set_trace(self, params: lsp_types.SetTraceParams) -> None:
        pass

    @implement_notify("$/cancelRequest")
    def cancel_request(self, params: lsp_types.CancelParams) -> None:
        pass

    @implement_notify("$/progress")
    def progress(self, params: lsp_types.ProgressParams) -> None:
        pass
