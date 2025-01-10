"""
Provides the MultilspyContext class, which stores the context for a Multilspy test.
"""

import dataclasses
from logging import Logger

from multilspy.multilspy_config import MultilspyConfig

# from multilspy.multilspy_logger import MultilspyLogger


@dataclasses.dataclass
class MultilspyContext:
    """
    Stores the context for a Multilspy test.
    """

    config: MultilspyConfig
    logger: Logger
    source_directory: str
