# -*- coding: utf-8 -*-
import atexit
import typing
from abc import ABCMeta, abstractmethod
from concurrent.futures import ALL_COMPLETED, wait
from concurrent.futures.thread import ThreadPoolExecutor
from dataclasses import dataclass

import anyio
from anyio import create_task_group


if typing.TYPE_CHECKING:
    from dharpa.processing.processing_module import ProcessingModule
    from dharpa.workflows.modules import InputItems, OutputItems, WorkflowModule

_DEFAULT_EXECUTOR = None


def set_default_executor(executor: "Processor"):
    global _DEFAULT_EXECUTOR
    _DEFAULT_EXECUTOR = executor


def get_default_executor() -> typing.Optional["Processor"]:
    return _DEFAULT_EXECUTOR


@dataclass
class ProcessingBundle(object):

    processing_module: "ProcessingModule"
    inputs: "InputItems"
    outputs: "OutputItems"


class Processor(metaclass=ABCMeta):
    @abstractmethod
    async def process(self, *modules: "WorkflowModule"):
        pass


class AsyncProcessor(Processor):
    async def process(
        self,
        *modules: "WorkflowModule",
    ):
        async with create_task_group() as tg:
            for m in modules:
                await tg.spawn(m.process)


class ThreadPoolProcessor(Processor):
    def __init__(self, max_workers: int = None):

        self._max_workers: typing.Optional[int] = max_workers
        self._threadpool: ThreadPoolExecutor = None  # type: ignore

    @property
    def threadpool(self):
        if self._threadpool is None:
            self._threadpool = ThreadPoolExecutor(max_workers=self._max_workers)
            atexit.register(self._threadpool.shutdown, wait=False)
        return self._threadpool

    async def process(
        self,
        *modules: "WorkflowModule",
    ):
        def run(callable, *args):
            anyio.run(callable, *args)

        futures = []
        for m in modules:
            if m.is_workflow:
                future = self.threadpool.submit(run, m.process, self)
            else:
                future = self.threadpool.submit(run, m.process)
            futures.append(future)

        wait(futures, timeout=None, return_when=ALL_COMPLETED)
