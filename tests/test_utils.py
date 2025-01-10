import contextlib
import logging
import os
import pathlib
from typing import Iterator
from uuid import uuid4

from multilspy.multilspy_config import MultilspyConfig
from multilspy.multilspy_utils import FileUtils
from tests.multilspy.multilspy_context import MultilspyContext


@contextlib.contextmanager
def create_test_context(params: dict) -> Iterator[MultilspyContext]:
    """
    Creates a test context for the given parameters.
    """
    config = MultilspyConfig.from_dict(params)
    logger = logging.getLogger("multilspy")
    user_home_dir = os.path.expanduser("~")
    multilspy_home_directory = str(pathlib.Path(user_home_dir, ".multilspy"))
    temp_extract_directory = str(pathlib.Path(multilspy_home_directory, uuid4().hex))
    try:
        os.makedirs(temp_extract_directory, exist_ok=False)
        assert params["repo_url"].endswith("/")
        repo_zip_url = params["repo_url"] + f"archive/{params['repo_commit']}.zip"
        FileUtils.download_and_extract_archive(
            repo_zip_url, temp_extract_directory, "zip", logger
        )
        dir_contents = os.listdir(temp_extract_directory)
        assert len(dir_contents) == 1
        source_directory_path = str(
            pathlib.Path(temp_extract_directory, dir_contents[0])
        )

        yield MultilspyContext(config, logger, source_directory_path)
    finally:
        pass
        # if os.path.exists(temp_extract_directory):
        #     shutil.rmtree(temp_extract_directory)
