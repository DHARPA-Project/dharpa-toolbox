# -*- coding: utf-8 -*-
import os
import sys

from appdirs import AppDirs


dharpa_toolbox_app_dirs = AppDirs("dharpa_toolbox", "frkl")

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
