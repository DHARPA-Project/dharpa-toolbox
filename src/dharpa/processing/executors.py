# -*- coding: utf-8 -*-
from abc import ABCMeta, abstractmethod

from dharpa.processing.processing_module import ProcessingModule
from dharpa.workflows.modules import InputItems, OutputItems


class Executor(metaclass=ABCMeta):
    @abstractmethod
    def execute(
        self,
        processing_module: ProcessingModule,
        inputs: InputItems,
        outputs: OutputItems,
    ):
        pass


class InThreadExecutor(Executor):
    def execute(
        self,
        processing_module: ProcessingModule,
        inputs: InputItems,
        outputs: OutputItems,
    ):

        processing_module.process(inputs=inputs, outputs=outputs)
