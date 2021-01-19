# -*- coding: utf-8 -*-
from abc import ABCMeta
from typing import Iterable, Mapping

from dharpa_toolbox.modules.core import DharpaModule, ValueLocation
from ipywidgets import Widget


class ModuleWidget(metaclass=ABCMeta):
    def __init__(self, module: DharpaModule):

        self._module: DharpaModule = module


class TextPreprocessingSettingsInputWidget(ModuleWidget):
    def required_input_names(self) -> Iterable[str]:

        return ["enable_lowercase", "remove_stopwords", "stopwords_list"]

    def required_output_names(self) -> Iterable[str]:

        return ["file_set"]

    def _create_widget(
        self,
        input_items: Mapping[str, ValueLocation],
        output_items: Mapping[str, ValueLocation],
    ) -> Widget:

        pass
