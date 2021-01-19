# -*- coding: utf-8 -*-
from dharpa_toolbox.modules.workflows import DharpaWorkflow


class PlainWorkflowRenderer(object):
    def __init__(self, workflow: DharpaWorkflow):

        self._workflow: DharpaWorkflow = workflow

    def render(self):

        print(self._workflow._workflow_inputs)

        for index, stage in enumerate(self._workflow.execution_stages):

            print(f"Stage {index+1}")

            for module in stage:
                print(module)
