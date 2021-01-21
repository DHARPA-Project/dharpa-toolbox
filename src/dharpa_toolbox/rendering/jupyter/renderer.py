# -*- coding: utf-8 -*-
import typing

import traitlets
from IPython.core.display import Markdown, display
from dharpa_toolbox.modules.core import ValueLocation, ValueLocationType
from dharpa_toolbox.modules.workflows import DharpaWorkflow
from dharpa_toolbox.rendering.jupyter.item_widgets import GenericViewer, ItemWidget
from dharpa_toolbox.rendering.jupyter.module_widgets import (
    CorpusProcessingModuleWidget,
    FileReaderModuleWidget,
)
from dharpa_toolbox.rendering.jupyter.utils import find_all_item_widget_classes
from ipywidgets import GridspecLayout, Label


INPUT_TYPE_WIDGET_MAP = {traitlets.Any: "inputfileswidget"}

widget_classes = find_all_item_widget_classes()


def sort_locations(workflow: DharpaWorkflow, type: ValueLocationType):

    result: typing.Dict[ValueLocation, ValueLocation] = {}

    if type == ValueLocationType.input:
        locs = workflow._workflow_inputs
    else:
        locs = workflow._workflow_outputs

    done: typing.Set[ValueLocation] = set()

    for stage in workflow.execution_stages:

        for module in stage:
            matched_locations = [
                loc for loc in locs.values() if loc.module == module and loc not in done
            ]
            done.update(matched_locations)

            for m in matched_locations:
                result[locs.inverse[m]] = m

    return result


class ModuleJupyterWorkflowRenderer(object):
    def __init__(self, workflow: DharpaWorkflow):

        self._workflow: DharpaWorkflow = workflow

    def render(self):

        widgets = {}

        for module_name, module in self._workflow.modules.items():

            module_type = module._module_name

            if module_type == "file_reader":
                mw = FileReaderModuleWidget(module)
                widgets[module] = mw
            elif module_type == "corpus_processing":
                mw = CorpusProcessingModuleWidget(module)
                widgets[module] = mw
            else:
                raise ValueError(f"No module type: {module_type}")

        workflow_doc = f"# Workflow: {self._workflow.id}\n\n{self._workflow.__doc__}\n\n## Workflow modules"

        display(Markdown(workflow_doc))

        for i, (m, w) in enumerate(widgets.items()):
            m_doc = m.__doc__.strip().split("\n")[0]

            display(Markdown(f"### {i+1} - {m.id}"))
            display(Markdown(m_doc))

            # print(m.__doc__)
            display(w.widget)
            display(Markdown("---"))

        display(Markdown("# Results"))

        for output_name, loc in self._workflow.output_locations().items():
            display(Markdown(f"### ``{output_name}``"))
            viewer = GenericViewer(loc)
            display(viewer.widget)


class PlainJupyterWorkflowRenderer(object):
    def __init__(self, workflow: DharpaWorkflow):

        self._workflow: DharpaWorkflow = workflow

    def render(self):

        widgets: typing.Dict[str, ItemWidget] = {}

        locs_sorted = sort_locations(self._workflow, type=ValueLocationType.input)
        locs = {w_in.value_name: w_in for w_in in locs_sorted.keys()}

        for input_name, loc in locs.items():

            # input_name = w_in.value_name

            if input_name == "files":
                widget_cls: typing.Type = widget_classes["inputfileswidget"]
                widgets[input_name] = widget_cls(files=loc)
            elif input_name in ["make_lowercase", "remove_stopwords"]:
                widget_cls = widget_classes["checkboxwidget"]
                widgets[input_name] = widget_cls(item=loc)
            elif input_name == "stopwords":
                widget_cls = widget_classes["stringlistinputwidget"]
                widgets[input_name] = widget_cls(item=loc)
            elif input_name == "text_map":
                widget_cls = widget_classes["jsonimportwidget"]
                widgets[input_name] = widget_cls(item=loc)
            else:
                raise ValueError(f"Invalid input {input_name}")

        output_widgets: typing.Dict[str, ItemWidget] = {}

        for output_name, loc in self._workflow.output_locations().items():

            if output_name == "processed_text_corpus":
                widget_cls = widget_classes["genericviewer"]
                output_widgets[output_name] = widget_cls(loc)

        grid = GridspecLayout(len(widgets), 2)
        for i, (n, w) in enumerate(widgets.items()):
            grid[i, 0] = Label(value=n)
            grid[i, 1] = w.widget

        display(grid)

        for w in output_widgets.values():
            display(w.widget)
