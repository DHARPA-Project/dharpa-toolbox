# -*- coding: utf-8 -*-
# AUTOGENERATED! DO NOT EDIT! File to edit: notebooks/20_widgets.ipynb (unless otherwise specified).

# Cell
import json
from abc import ABCMeta, abstractmethod
from datetime import datetime
from functools import partial
from typing import Any, Dict, Iterable, Mapping

import rich
from dharpa_toolbox.modules.core import ValueLocationType
from dharpa_toolbox.modules.workflows import ValueLocation
from ipywidgets import Checkbox, FileUpload, Output, Textarea, ToggleButton, Widget


class ItemWidget(metaclass=ABCMeta):
    def __init__(self, *items: ValueLocation, **more_items: ValueLocation):

        # if input_item.type != ValueLocationType.workflow_input:
        #     raise ValueError(f"Invalid input item, can only use '{ValueLocationType.workflow_input}', not '{input_item.type}'")

        self._input_items: Dict[str, ValueLocation] = {}
        self._output_items: Dict[str, ValueLocation] = {}

        for ii in items:
            self._add_item(ii.value_name, ii)
        for k, v in more_items.items():
            self._add_item(k, v)

        missing_inputs = set()
        missing_outputs = set()
        for n in self.required_input_names():
            if n not in self._input_items.keys():
                missing_inputs.add(n)
        for n in self.required_output_names():
            if n not in self._output_items.keys():
                missing_outputs.add(n)

        if missing_inputs or missing_outputs:
            msg = "Can't create widget, missing items: "
            if missing_inputs:
                msg = msg + f" {', '.join(missing_inputs)} (inputs)"
            if missing_outputs:
                msg = msg + f" {', '.join(missing_outputs)} (outputs)"

            raise ValueError(msg)

        self._widget: Widget = None

    def required_input_names(self) -> Iterable[str]:
        return []

    def required_output_names(self) -> Iterable[str]:
        return []

    def _add_item(self, name: str, item: ValueLocation):

        if item.direction == ValueLocationType.input:
            if name in self._input_items.keys():
                raise ValueError(
                    f"Can't add input item to widget, duplicate item name: {name}"
                )

            self._input_items[name] = item
        else:
            if name in self._output_items.keys():
                raise ValueError(
                    f"Can't add output item to widget, duplicate item name: {name}"
                )
            self._output_items[name] = item

            func = partial(self.output_value_changed, name)

            item.module.state.outputs.observe(func, names=item.value_name)

    def set_input_item_value(self, value_name: str, change: Any):

        # print(f"Widget value set: {change}")

        change_value = self.input_value_to_be_changed(value_name, change)

        if change_value is None:
            return

        ii = self._input_items[value_name]
        ii.module.set_input(ii.value_name, change_value)

        self.input_value_changed(value_name, change, change_value)

    def input_value_to_be_changed(self, item_name: str, change):

        return change.new

    def input_value_changed(self, item_name: str, change, change_value):
        pass

    @property
    def widget(self) -> Widget:

        if self._widget is not None:
            return self._widget

        self._widget = self._create_widget(
            input_items=self._input_items, output_items=self._output_items
        )

        for name, loc in self._input_items.items():
            func = partial(self.set_input_item_value, name)
            self._widget.observe(func, names=name)
        return self._widget

    @abstractmethod
    def _create_widget(
        self,
        input_items: Mapping[str, ValueLocation],
        output_items: Mapping[str, ValueLocation],
    ) -> Widget:
        pass

    def output_value_changed(self, value_name: str, change: Any):

        pass


class ToggleButtonWidget(ItemWidget):
    def required_input_names(self) -> Iterable[str]:
        return ["item"]

    def _create_widget(
        self,
        input_items: Mapping[str, ValueLocation],
        output_items: Mapping[str, ValueLocation],
    ) -> Widget:

        toggle_button = ToggleButton(
            value=False, description=input_items["item"].value_name, icon="check"
        )

        def set_value(change):

            self.set_input_item_value("item", change)

        toggle_button.observe(set_value, names="value")
        return toggle_button


class StringListInputWidget(ItemWidget):
    def required_input_names(self) -> Iterable[str]:

        return ["item"]

    def input_value_to_be_changed(self, item_name: str, change):

        value = change.new
        result = value.split("\n")

        return result

    def _create_widget(
        self,
        input_items: Mapping[str, ValueLocation],
        output_items: Mapping[str, ValueLocation],
    ) -> Widget:

        textarea = Textarea(placeholder="< stopwords (one per line) >", disabled=False)

        def set_value(change):
            self.set_input_item_value("item", change)

        textarea.observe(set_value, names="value")
        return textarea


class JsonImportWidget(ItemWidget):
    def required_input_names(self) -> Iterable[str]:

        return ["item"]

    def input_value_to_be_changed(self, item_name: str, change):

        value = change.new
        try:
            result = json.loads(value)
            return result
        except Exception:
            return None
            # return change.old

    def _create_widget(
        self,
        input_items: Mapping[str, ValueLocation],
        output_items: Mapping[str, ValueLocation],
    ) -> Widget:

        textarea = Textarea(placeholder="< text_map_in_json >", disabled=False)

        def set_value(change):
            self.set_input_item_value("item", change)

        textarea.observe(set_value, names="value")
        return textarea


class CheckBoxWidget(ItemWidget):
    def required_input_names(self) -> Iterable[str]:
        return ["item"]

    def _create_widget(
        self,
        input_items: Mapping[str, ValueLocation],
        output_items: Mapping[str, ValueLocation],
    ) -> Widget:

        item = input_items["item"]

        checkbox = Checkbox(
            value=item.value,
            # description=input_items["item"].value_name,
            disabled=False,
        )

        def set_value(change):

            self.set_input_item_value("item", change)

        checkbox.observe(set_value, names="value")
        return checkbox


class InputFilesWidget(ItemWidget):
    def _create_widget(
        self,
        input_items: Mapping[str, ValueLocation],
        output_items: Mapping[str, ValueLocation],
    ) -> Widget:

        # uploaded_file_details = Output()
        file_upload = FileUpload(accept=".csv", multiple=True)
        file_upload = FileUpload(multiple=True)

        def set_files(change):

            self.set_input_item_value("files", change)
            self.widget._counter = len(change.new)

        file_upload.observe(set_files, names="value")

        return file_upload


class GenericViewer(ItemWidget):
    def _create_widget(
        self,
        input_items: Mapping[str, ValueLocation],
        output_items: Mapping[str, ValueLocation],
    ) -> Widget:

        output = Output()
        return output

    def output_value_changed(self, item_name: str, change):

        self.widget.clear_output()

        with self.widget:
            rich.jupyter.print(f"Updated: {datetime.now()}")

            rich.jupyter.print(change.new)


class FileSetTable(ItemWidget):
    def _create_widget(
        self,
        input_items: Mapping[str, ValueLocation],
        output_items: Mapping[str, ValueLocation],
    ) -> Widget:

        output = Output()
        return output

    def output_value_changed(self, item_name: str, change):

        self.widget.clear_output()

        with self.widget:

            files = change.new

            for id, text in files.items():
                _t = str(text)
                if len(_t) > 53:
                    _t = _t[0:50] + "..."
                print(f"{id}: {_t}")


# class TextCorpusViewer(ItemWidget):
#     def _create_widget(
#         self,
#         input_items: Mapping[str, ValueLocation],
#         output_items: Mapping[str, ValueLocation],
#     ) -> Widget:
#
#         output = Output()
#         return output
#
#     def output_value_changed(self, item_name: str, change: Any):
#
#         self.widget.clear_output()
#
#         with self.widget:
#             print(f"Updated: {datetime.now()}")
#             tc: TextCorpus = change.new
#             for id, text in tc.corpus().items():
#
#                 if len(text) < 20:
#                     t = text
#                 else:
#                     t = f"{text[0:20]}..."
#                 print(f'{id}: "{t}"')