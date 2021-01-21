# -*- coding: utf-8 -*-
import csv
import typing
from abc import ABCMeta, abstractmethod
from functools import partial

from dharpa_toolbox.modules.core import DharpaModule, ValueLocation, ValueLocationType
from dharpa_toolbox.modules.text import TextPreprocessingModule, TokenizeCorpusModule
from dharpa_toolbox.modules.utils import create_module
from dharpa_toolbox.modules.workflows import DharpaWorkflow
from ipywidgets import FileUpload, GridspecLayout, Widget, widgets


class ModuleWidget(metaclass=ABCMeta):
    def __init__(self, module: DharpaModule):

        self._module: DharpaModule = module
        self._widget: Widget = None

    @property
    def module(self) -> DharpaModule:
        return self._module

    @property
    def widget(self) -> Widget:
        if self._widget is None:
            self._widget = self._create_widget()
        return self._widget

    @abstractmethod
    def _create_widget(self) -> Widget:
        pass


class FileReaderModuleWidget(ModuleWidget):
    def __init__(self, module: DharpaModule):

        super().__init__(module)

    def _create_widget(self) -> Widget:

        file_upload = FileUpload(multiple=True)

        def set_files(change):

            self._module.set_input("files", change.new)
            self._module.process()
            file_upload._counter = len(change.new)

        file_upload.observe(set_files, names="value")
        label = widgets.Label(value="Upload text data")

        grid = GridspecLayout(1, 6, height="50px")
        grid[0, 0] = label
        grid[0, 1:] = file_upload

        return grid


class CorpusProcessingModuleWidget(ModuleWidget):

    _supported_module_types = "corpus_processing"

    def __init__(self, module: DharpaModule):

        self._processing_widgets: typing.Dict[str, Widget] = {}

        self._dummy_workflow: DharpaWorkflow = create_module("corpus_processing")  # type: ignore
        self._dummy_workflow.set_input("text_map", {"item": "Hello World!"})
        self._dummy_workflow.set_input("stopwords", [])

        super().__init__(module)

    def create_widget_for_processing_module(self, module: TextPreprocessingModule):

        checkbox = widgets.Checkbox(
            description=module.id, value=module._state.inputs.enabled
        )
        label = widgets.Label(value="")
        textfield = widgets.Textarea(value="", layout=widgets.Layout(height="150px"))
        textfield.disabled = True

        # def enable_step(change):
        #     module.set_input("enabled", change.new)
        #     module.process()
        # checkbox.observe(enable_step, names="value")

        def set_text(change):

            enabled = module._state.inputs.enabled
            if enabled:
                val = change.new["item"]
                textfield.value = "\n".join(val)

                label.value = f"Number of tokens: {len(val)}"
            else:
                textfield.value = "-- not enabled --"
                label.value = ""

        module._state.outputs.observe(set_text, names="tokenized_text")

        vbox = widgets.VBox((checkbox, label, textfield))

        return {
            "module": module,
            "vbox": vbox,
            "checkbox": checkbox,
            "textfield": textfield,
        }

    def _create_widget(
        self,
    ) -> Widget:

        tokenize_module = None

        # preview text selection

        text_preview_select_widget = widgets.Dropdown(
            description="",
            # placeholder='Choose Someone',
            options=["No sources yet..."],
            disabled=False,
        )

        def texts_changed(change):
            values = tuple(change.new.keys())
            text_preview_select_widget.options = values

        self.module._state.inputs.observe(texts_changed, names="text_map")

        # stopword upload
        file_upload = FileUpload(multiple=False)
        stopword_label_1 = widgets.Label(value="Upload stopwords")
        stopword_label_2 = widgets.Label(value="")

        def stopwords_changed(change):

            file_name = next(iter(change.new))
            file_data = change.new[file_name]["content"]

            stopwords_string = str(file_data, "utf-8")

            reader = csv.reader(stopwords_string.split("\n"))
            stopwords = []
            for row in reader:
                if not row or row == ["stopword"]:
                    continue
                stopwords.append(row[0])

            self._dummy_workflow.set_input("stopwords", stopwords)
            stopword_label_2.value = f"Number of stopwords: {len(stopwords)}"

        file_upload.observe(stopwords_changed, names="value")

        # text processiing

        def enabled_changed(module, change):

            loc = ValueLocation(
                module=module, value_name="enabled", direction=ValueLocationType.input
            )
            workflow_input = self._dummy_workflow._workflow_inputs.inverse[loc]

            self._dummy_workflow.set_input(workflow_input.value_name, change.new)

        for name, module in self._dummy_workflow.modules.items():

            if issubclass(module.__class__, TokenizeCorpusModule):
                tokenize_module = module
            elif issubclass(module.__class__, TextPreprocessingModule):
                self._processing_widgets[
                    name
                ] = self.create_widget_for_processing_module(
                    module  # type: ignore
                )  # type: ignore
                checkbox = self._processing_widgets[name]["checkbox"]
                func = partial(enabled_changed, module)
                checkbox.observe(func, names="value")

        assert tokenize_module is not None

        def text_selection_changed(change):

            value = self.module._state.inputs.text_map[change.new]
            self._dummy_workflow.set_input("text_map", {"item": value})

        text_preview_select_widget.observe(text_selection_changed, names="value")

        grid = GridspecLayout(12, 6, height="400px")

        processings_container = widgets.HBox(
            [s["vbox"] for s in self._processing_widgets.values()],
            layout=widgets.Layout(justify_content="flex-start"),
        )

        process_button = widgets.Button(description="Process")

        def start_process(source):

            with self.module._state.inputs.hold_trait_notifications():
                for input_name in self._dummy_workflow.input_names:

                    if input_name == "text_map":
                        continue

                    value = self._dummy_workflow.get_input_location(input_name).value
                    self.module.set_input(input_name, value)

            # self.module.process()

        process_button.on_click(start_process)

        grid[0, 0] = widgets.Label(value="Select preview item")
        grid[0, 1] = text_preview_select_widget
        grid[1, 0] = stopword_label_1
        grid[1, 1] = file_upload
        grid[2, 1] = stopword_label_2
        grid[3:11, 0:] = processings_container
        grid[11, 2] = process_button

        return grid
