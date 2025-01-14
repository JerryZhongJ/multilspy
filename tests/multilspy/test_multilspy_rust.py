"""
This file contains tests for running the Rust Language Server: rust-analyzer
"""

import asyncio
import os
import tempfile
import unittest
from pathlib import PurePath

import pytest

from multilspy import LanguageServer
from multilspy.multilspy_config import Language, MultilspyConfig
from multilspy.multilspy_types import CompletionItemKind, Location
from tests.test_utils import create_test_context

pytest_plugins = ("pytest_asyncio",)


@pytest.mark.asyncio
async def test_multilspy_rust_carbonyl():
    """
    Test the working of multilspy with rust repository - carbonyl
    """
    code_language = Language.RUST
    params = {
        "code_language": code_language,
        "repo_url": "https://github.com/fathyb/carbonyl/",
        "repo_commit": "ab80a276b1bd1c2c8dcefc8f248415dfc61dc2bf",
    }
    with create_test_context(params) as context:
        lsp = LanguageServer.create(context.config, context.source_directory)

        # All the communication with the language server must be performed inside the context manager
        # The server process is started when the context manager is entered and is terminated when the context manager is exited.
        # The context manager is an asynchronous context manager, so it must be used with async with.
        async with lsp.running():
            result = await lsp.request_definition(
                str(PurePath("src/browser/bridge.rs")), 132, 18
            )

            assert isinstance(result, list)
            assert len(result) == 1
            item = result[0]
            assert item.relativePath == str(PurePath("src/input/tty.rs"))
            assert (
                item.range.start.line == 43
                and item.range.start.character == 4
                and item.range.end.line == 59
                and item.range.end.character == 5
            )

            assert isinstance(result, list)
            assert len(result) == 1
            item = result[0]
            assert item.relativePath == str(PurePath("src/input/tty.rs"))
            assert (
                item.range.start.line == 43
                and item.range.start.character == 4
                and item.range.end.line == 59
                and item.range.end.character == 5
            )
            result = await lsp.request_references(
                str(PurePath("src/input/tty.rs")), 43, 15
            )

            assert isinstance(result, list)
            assert len(result) == 2

            for item in result:
                item.uri = ""
                item.absolutePath = ""

            case = unittest.TestCase()
            case.assertCountEqual(
                result,
                [
                    Location.model_validate(
                        {
                            "relativePath": str(PurePath("src/browser/bridge.rs")),
                            "range": {
                                "start": {"line": 132, "character": 13},
                                "end": {"line": 132, "character": 21},
                            },
                            "uri": "",
                            "absolutePath": "",
                        }
                    ),
                    Location.model_validate(
                        {
                            "relativePath": str(PurePath("src/input/tty.rs")),
                            "range": {
                                "start": {"line": 16, "character": 13},
                                "end": {"line": 16, "character": 21},
                            },
                            "uri": "",
                            "absolutePath": "",
                        }
                    ),
                ],
            )


@pytest.mark.asyncio
async def test_multilspy_rust_completions_mediaplayer() -> None:
    """
    Test the working of multilspy with Rust repository - mediaplayer
    """
    code_language = Language.RUST
    params = {
        "code_language": code_language,
        "repo_url": "https://github.com/LakshyAAAgrawal/MediaPlayer_example/",
        "repo_commit": "ba27bb16c7ba1d88808300364af65eb69b1d84a8",
        # "trace_lsp_communication": True,
    }

    with create_test_context(params) as context:
        lsp = LanguageServer.create(
            context.config, context.source_directory, context.logger
        )
        filepath = "src/playlist.rs"
        # All the communication with the language server must be performed inside the context manager
        # The server process is started when the context manager is entered and is terminated when the context manager is exited.
        async with lsp.running():
            with lsp.file_opened(filepath):
                #             deleted_text = lsp.delete_text_between_positions(
                #                 filepath,
                #                 Position(line=10, character=40),
                #                 Position(line=12, character=4),
                #             )
                #             assert (
                #                 deleted_text
                #                 == """reset();
                #     media_player1 = media_player;
                # """
                # )
                response = await lsp.request_completions(
                    filepath, 10, 40, allow_incomplete=True
                )

                response = [
                    item for item in response if item.kind != CompletionItemKind.Snippet
                ]
                completionTexts = set()
                for item in response:
                    completionTexts.add(
                        item.completionText[: item.completionText.find("(")]
                    )

                assert completionTexts == {
                    "reset",
                    "into",
                    "try_into",
                    "prepare",
                }


@pytest.mark.asyncio
async def test_tmp_completion() -> None:
    """
    Test the working of multilspy with Rust repository - mediaplayer
    """

    with tempfile.TemporaryDirectory() as temp_dir:
        with open(os.path.join(temp_dir, "Cargo.toml"), "w") as f:
            f.write(
                """[package]
name = "tinyhttpd"
version = "0.1.0"
authors = [ "Your Name <youremail@example.com>",]
edition = "2021"
"""
            )
        os.mkdir(os.path.join(temp_dir, "src"))
        filepath = os.path.join("src", "main.rs")
        with open(os.path.join(temp_dir, filepath), "w") as f:
            f.write(
                """fn main() {
    let s = "hello world";
    s.len();
}"""
            )

        lsp = LanguageServer.create(
            MultilspyConfig(Language.RUST, True),
            temp_dir,
        )

        async with lsp.running():

            with lsp.file_opened(filepath):

                response = await lsp.request_completions(
                    filepath, 2, 6, allow_incomplete=True
                )

                response = [
                    item for item in response if item.kind != CompletionItemKind.Snippet
                ]

                for item in response:
                    completionText = item.completionText[
                        : item.completionText.find("(")
                    ]
                    print(completionText)


if __name__ == "__main__":
    asyncio.run(test_tmp_completion())
