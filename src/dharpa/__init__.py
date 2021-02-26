# -*- coding: utf-8 -*-

import logging
import os
import typing

from dharpa.defaults import DHARPA_TOOLBOX_DEFAULT_WORKFLOWS_FOLDER


if typing.TYPE_CHECKING:
    from dharpa.processing.processing_module import ProcessingModule
    from dharpa.workflows.workflow import WorkflowProcessingModule


log = logging.getLogger("dharpa")

"""Top-level package for dharpa-toolbox."""

__author__ = """Markus Binsteiner"""
__email__ = "markus.binsteiner@uni.lu"

__all__ = ["get_version", "ModuleCollection", "DHARPA_MODULES", "create_workflow"]


def get_version():
    from pkg_resources import DistributionNotFound, get_distribution

    try:
        # Change here if project is renamed and does not equal the package name
        dist_name = __name__
        __version__ = get_distribution(dist_name).version
    except DistributionNotFound:

        try:
            version_file = os.path.join(os.path.dirname(__file__), "version.txt")

            if os.path.exists(version_file):
                with open(version_file, encoding="utf-8") as vf:
                    __version__ = vf.read()
            else:
                __version__ = "unknown"

        except (Exception):
            pass

        if __version__ is None:
            __version__ = "unknown"

    return __version__


class ModuleCollection(object):
    def __init__(self):
        self._module_classes: typing.Dict[str, typing.Type["ProcessingModule"]] = None  # type: ignore
        self._workflow_configs: typing.Dict[str, typing.Dict[str, typing.Any]] = None  # type: ignore

    def get_module_classes(
        self,
    ) -> typing.Mapping[str, typing.Type["ProcessingModule"]]:

        if self._module_classes is None:
            from dharpa.workflows.utils import find_all_processing_module_classes

            self._module_classes = find_all_processing_module_classes()
        return self._module_classes

    def get_workflow_configs(
        self,
    ) -> typing.Mapping[str, typing.Mapping[str, typing.Any]]:

        if self._workflow_configs is None:
            from dharpa.workflows.utils import find_workflow_descriptions

            self._workflow_configs = find_workflow_descriptions(
                DHARPA_TOOLBOX_DEFAULT_WORKFLOWS_FOLDER
            )
        return self._workflow_configs

    def get(
        self, key: str, raise_exception: bool = True
    ) -> typing.Optional[typing.Type["ProcessingModule"]]:

        result: typing.Optional[
            typing.Type[ProcessingModule]
        ] = self.get_module_classes().get(key, None)
        if result is None:

            result_2: typing.Optional[
                typing.Mapping[str, typing.Any]
            ] = self.get_workflow_configs().get(key, None)

            if result_2 is None and raise_exception:
                raise Exception(
                    f"No module or workflow with type '{key}' available. Existing types: {', '.join(self.all_names)}"
                )
            elif result_2 is None:
                return None

            return self.get_workflow(key, raise_exception=raise_exception)

        if result is None and raise_exception:
            raise Exception(
                f"No module with type '{key}' available. Existing module types: {', '.join(self.all_names)}"
            )

        return result

    def get_module(
        self, key: str, raise_exception: bool = True
    ) -> typing.Optional[typing.Type["ProcessingModule"]]:

        result = self.get_module_classes().get(key, None)
        if result is None and raise_exception:
            raise Exception(
                f"No module with type '{key}' loaded. Available modules: {', '.join(self.module_names)}"
            )

        return result

    def get_workflow(
        self, key: str, raise_exception: bool = True
    ) -> typing.Optional[typing.Type["WorkflowProcessingModule"]]:

        result = self.get_workflow_configs().get(key, None)
        if result is None and raise_exception:
            raise Exception(
                f"No workflow with type '{key}' available. Existing workflow: {', '.join(self.workflow_names)}"
            )
        elif result is None:
            return None

        if self.get_workflow_configs()[key].get("config", None) is None:
            from dharpa.models import ProcessingConfig

            pc = ProcessingConfig(
                module_type="workflow", config=self._workflow_configs[key]["data"]
            )
            self._workflow_configs[key]["config"] = pc

        if self.get_workflow_configs()[key].get("cls", None) is None:
            from dharpa.workflows.utils import (
                generate_workflow_processing_class_from_config,
            )

            self._workflow_configs[key][
                "cls"
            ] = generate_workflow_processing_class_from_config(
                key, self._workflow_configs[key]["config"]
            )
        return self._workflow_configs[key]["cls"]

    @property
    def module_names(self) -> typing.Iterable[str]:
        return self._module_classes.keys()

    @property
    def workflow_names(self) -> typing.Iterable[str]:
        return self._workflow_configs.keys()

    @property
    def all_names(self) -> typing.Iterable[str]:
        return list(self.get_module_classes().keys()) + list(
            self.get_workflow_configs().keys()
        )


DHARPA_MODULES = ModuleCollection()


def create_workflow(module_type: str, workflow_alias: typing.Optional[str] = None):

    from dharpa.workflows.workflow import DharpaWorkflow
    from dharpa.models import ProcessingConfig

    config = ProcessingConfig(module_type=module_type)
    w = DharpaWorkflow(processing_config=config, alias=workflow_alias)
    return w
