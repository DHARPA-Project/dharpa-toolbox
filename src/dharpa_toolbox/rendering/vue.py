# -*- coding: utf-8 -*-
from dharpa_toolbox.modules.workflows import DharpaWorkflow


class VueRenderer(object):
    def __init__(self, workflow: DharpaWorkflow):

        self._workflow: DharpaWorkflow = workflow
