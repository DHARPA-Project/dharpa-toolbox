# -*- coding: utf-8 -*-
from dharpa_toolbox.rendering.jupyter.item_widgets import ItemWidget
from dharpa_toolbox.utils import get_subclass_map


def find_all_item_widget_classes():
    modules_to_load = [
        "dharpa_toolbox.modules.core",
        "dharpa_toolbox.modules.files",
        "dharpa_toolbox.modules.text",
    ]

    all_classes = get_subclass_map(
        ItemWidget,
        preload_modules=modules_to_load,
        override_duplicate_class=True,
    )
    return all_classes
