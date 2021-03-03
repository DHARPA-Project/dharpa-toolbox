# -*- coding: utf-8 -*-
import os
import sys
from appdirs import AppDirs

dharpa_app_dirs = AppDirs("dharpa", "dharpa")

if not hasattr(sys, "frozen"):
    DHARPA_TOOLBOX_MODULE_BASE_FOLDER = os.path.dirname(__file__)
    """Marker to indicate the base folder for the `dharpa_toolbox` module."""
else:
    DHARPA_TOOLBOX_MODULE_BASE_FOLDER = os.path.join(
        sys._MEIPASS, "dharpa_toolbox"  # type: ignore
    )
    """Marker to indicate the base folder for the `dharpa_toolbox` module."""

DHARPA_TOOLBOX_RESOURCES_FOLDER = os.path.join(
    DHARPA_TOOLBOX_MODULE_BASE_FOLDER, "resources"
)

DHARPA_TOOLBOX_DEFAULT_WORKFLOWS_FOLDER = os.path.join(
    DHARPA_TOOLBOX_RESOURCES_FOLDER, "workflows"
)

VALID_WORKFLOW_FILE_EXTENSIONS = ["yaml", "yml", "json"]
DEFAULT_MODULES_TO_LOAD = (
    "dharpa.processing.core.logic_gates",
    "dharpa.processing.core.dummy",
)

MODULE_TYPE_KEY = "module_type"
MODULE_TYPE_NAME_KEY = "module_type_name"

DEFAULT_EXCLUDE_DIRS = [".git", ".tox", ".cache"]
"""List of directory names to exclude by default when walking a folder recursively."""
