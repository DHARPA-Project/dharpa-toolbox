# -*- coding: utf-8 -*-

__all__ = ["DharpaWorkflow"]

# Cell
import collections.abc
import copy
import json
import logging
import os
import typing
from functools import partial
from pathlib import Path
from typing import Mapping

import networkx as nx
import yaml
from bidict import bidict
from dharpa_toolbox.modules.core import DharpaModule, ValueLocation, ValueLocationType
from dharpa_toolbox.modules.utils import find_all_module_classes
from dharpa_toolbox.utils import to_camel_case
from traitlets import HasTraits


# export

log = logging.getLogger("dharpa-toolbox")


class DharpaWorkflow(DharpaModule):
    @classmethod
    def from_file(cls, path: typing.Union[str, Path], id: typing.Optional[str] = None):

        if isinstance(path, str):
            path = Path(os.path.expanduser(path))

        content = path.read_text()

        if path.name.endswith(".json"):
            content_type = "json"
        elif path.name.endswith(".yaml") or path.name.endswith(".yml"):
            content_type = "yaml"
        else:
            raise ValueError(
                "Invalid file format, only 'json' and 'yaml' supported for now."
            )

        if content_type == "json":
            config = json.loads(content)
        else:
            config = yaml.safe_load(content)

        if id:
            config["id"] = id

        return DharpaWorkflow(**config)

    def __init__(self, **config: typing.Any):

        self._module_details: typing.Dict[str, typing.Dict[str, typing.Any]] = {}

        self._execution_graph: nx.DiGraph = None  # type: ignore
        """A graph that shows dependencies between modules."""
        self._data_flow_graph: nx.DiGraph = None  # type: ignore
        """A graph to show the flow of the data through the workflow. Inputs are connected to modules, which are
        connected to outputs, wich in turns can be connected to other modules' inputs."""

        self._workflow_inputs: bidict[ValueLocation, ValueLocation] = None  # type: ignore
        """A map of all this workflows inputs (all inputs that are not connected to other modules outputs."""
        self._workflow_outputs: bidict[ValueLocation, ValueLocation] = None  # type: ignore
        """A map of all this workflows outputs (all outputs that are mentioned in the 'workflow_outputs' config section
        of a module."""

        self._execution_stages: typing.Iterable[typing.Iterable[DharpaModule]] = None  # type: ignore
        """A list of lists of modules, in order of their level of execution."""

        super().__init__(**config)

    def _workflow_input_updated(
        self, workflow_input: ValueLocation, change
    ) -> typing.Any:

        assert workflow_input.direction == ValueLocationType.input

        self._add_module_event(
            f"Input updated for workflow: {workflow_input.value_name}"
        )

        input_loc = self._workflow_inputs[workflow_input]
        module_obj = input_loc.module
        input_name = input_loc.value_name

        self._add_module_event(
            f"forwarding workflow input '{workflow_input.value_name}' to internal module input: {module_obj.id}.{input_name}"
        )

        trait = module_obj._state.inputs.traits().get(input_name)
        trait.set(module_obj._state.inputs, change.new)

        module_obj.process()

        self._is_stale()

    def _module_output_updated(self, module_output: ValueLocation, change) -> None:

        assert module_output.direction == ValueLocationType.output

        self._add_module_event(f"Internal module output updated: {module_output}")
        out_edges = self.data_flow_graph.out_edges(module_output)
        modules_to_process: typing.Set[DharpaModule] = set()
        workflow_outputs_to_set: typing.Set[ValueLocation] = set()
        updated_edges: typing.Set[str] = set()
        for oe in out_edges:
            target: ValueLocation = oe[1]

            if target.module == self:
                workflow_outputs_to_set.add(target)
            elif target.direction == ValueLocationType.input:
                updated_edges.add(str(target))

                target.module.set_input(target.value_name, change.new)
                modules_to_process.add(target.module)
            elif target.direction == ValueLocationType.output and (
                isinstance(target.module, DharpaWorkflow)
                or issubclass(target.module.__class__, DharpaWorkflow)
            ):
                raise NotImplementedError()
                # setting workflow output
                workflow_outputs_to_set.add(target)
                # target.module._workflow_output_updated(workflow_output=target, module_output=module_output, change=change)
            else:
                raise Exception("Invalid value location")

        self._add_module_event(
            f"Updated out edges of module output '{module_output}': {updated_edges}"
        )
        self._add_module_event(
            f"Processing changed modules: {', '.join((str(m) for m in modules_to_process))}"
        )

        for m in modules_to_process:
            m.process()

        self._add_module_event("Proceesing of changed modules finished.")

        self._is_stale()

        for target in workflow_outputs_to_set:
            self._add_module_event(f"Setting workflow target output: {target}")
            source = self._workflow_outputs[target]
            target.module._state.outputs.set_trait(
                target.value_name, source.module.get_output(source.value_name)
            )

            # target_value = oe[1].module

        # print("OUT EDGES")
        # for oe in out_edges:
        #     target_module = oe[1].module
        #     target_value = oe[1].value_name
        #     print(f"{target_module} - {target_value}")
        #     print(workflow_output)
        # target_module.set_input(target_value, change.new)

        # workflow_output = self._workflow_outputs.inverse.get(module_output, None)
        # if workflow_output:
        #     self._workflow_output_updated(
        #         workflow_output=workflow_output,
        #         module_output=module_output,
        #         change=change,
        #     )

    def _is_stale(self) -> bool:

        for module in self.modules.values():
            if module.stale:
                self._state.stale = True
                return True

            # for target, source in self._workflow_outputs.items():
            #     target.module.set_input(target.value_name, getattr(source.module.output_names, source.value_name))

        self._state.stale = False
        return False

    # def _workflow_output_updated(
    #     self, workflow_output: ValueLocation, module_output: ValueLocation, change
    # ):
    #
    #     self._add_module_event(f"Output '{change.name}' for internal module '{module_output}' updated, setting workflow output '{workflow_output}'")
    #     workflow_output.module._state.outputs.set_trait(workflow_output.value_name, change.new)
    #
    #     # if self._state.busy:
    #         # means the workflow is currently processing
    #     # pass

    def _preprocess_config(self, **config: typing.Any):
        """The core method of a workflow, this connects all the modules, their inputs and outputs.

        TODO: details
        """

        # the first time this is run is different, because it is allowed for modules to not have an id (one will
        # be assigned automatically if missing)
        no_modules_yet = len(self._module_details) == 0

        # TODO: re-use already existing modules? If, then the following line needs to be removed.
        self._module_details.clear()

        # (re-)initialize the internal properties of this workflow
        self._workflow_inputs = bidict()
        self._workflow_outputs = bidict()

        self._execution_graph = nx.DiGraph()
        self._data_flow_graph = nx.DiGraph()

        self._execution_stages = []

        modules = config.get("modules", None)
        if not modules:
            # raise ValueError("Can't create workflow: no modules specified")
            return {}

        module_ids = set()

        m: typing.Dict[str, typing.Any]
        for m in modules:

            module_type = m["type"]
            module_config = m.get("config", {})
            module_id = m.get("id", None)
            module_input_map = m.get("input_map", {})
            # TODO: auto-fill all module outputs (and generate names automatically) if no 'workflow_output' is specified
            workflow_output_map = m.get("workflow_outputs", {})

            # retrieve the module class
            if isinstance(module_type, str):
                module_cls = find_all_module_classes().get(module_type)
            elif isinstance(module_type, type):
                module_cls = module_type
            else:
                raise TypeError(f"Invalid class for module type: {type(module_type)}")

            if not module_cls:
                raise Exception(f"No module '{module_type}' registered.")

            # auto-generate a module_id if necessary, and create or retrieve the module object
            if module_id is None:
                if not no_modules_yet:
                    raise Exception(
                        f"Module config without 'id' property not allowed after initial creation of workflow: {m}"
                    )
                module_obj = module_cls(**module_config)
                module_id = module_obj.id
                self._module_details[module_id] = {
                    "module": module_obj,
                }
                m["id"] = module_id
            elif module_id not in self._module_details.keys():
                if module_id in module_ids:
                    raise Exception(f"Duplicate module id: {module_id}")

                module_obj = module_cls(id=module_id, **module_config)
                self._module_details[module_id] = {
                    "module": module_obj,
                }
            else:
                # this is not used currently
                raise NotImplementedError()
                if module_id in module_ids:
                    raise ValueError(f"Duplicate module id: {module_id}")

                module_obj = self._module_details[module_id]["module"]
                # TODO: unobserve all inputs and outputs

                module_obj.set_config(module_config)
                # TODO: remove current input map

            module_ids.add(module_id)

            # creating a map of all inputs and their connections
            module_full_input_map = {}
            for name in module_obj._state.inputs.trait_names():

                # now we 'explode' the value of the input from the 'input_map' (if present). This allows the
                # configuration itself to be as minimal as possible:
                #  - if no or an empty value is present, the input will be connected to the workflow, with an
                #       auto-generated name
                #  - if the value is a string, it will be assumed to be the module name that holds the output to
                #       to connect to, and that output name is assumed to be the same as the input name
                #  - if the values is an iterable with the length of 2, the first item will be assumed to be the
                #       module name to connect to, and the 2nd one the name of the output name to connect to
                mapped_input_raw = module_input_map.get(name, None)
                if mapped_input_raw is None:
                    _output_name = f"{module_id}__{name}"
                    mapped_input = {"workflow_input": _output_name}
                elif isinstance(mapped_input_raw, str):

                    tokens = mapped_input_raw.split(".")
                    if len(tokens) != 2:
                        raise ValueError(
                            f"Can't parse mapped output '{mapped_input_raw}': only one seperator '.' allowed"
                        )
                    if "." in mapped_input_raw:
                        if (
                            tokens[0] == "workflow_input"
                            or tokens[0] == "__workflow_input__"
                        ):
                            mapped_input = {"workflow_input": tokens[1]}
                        else:
                            mapped_input = {
                                "module": tokens[0],
                                "output_name": tokens[1],
                            }
                    else:
                        mapped_input = {"module": mapped_input_raw, "output_name": name}
                elif isinstance(mapped_input_raw, collections.abc.Mapping):
                    mapped_input = dict(mapped_input_raw)
                    if (
                        "output_name" not in mapped_input.keys()
                        and "module" in mapped_input.keys()
                    ):
                        mapped_input["output_name"] = name

                elif (
                    isinstance(mapped_input_raw, collections.abc.Iterable)
                    and len(list(mapped_input_raw)) == 2
                ):
                    temp = list(mapped_input_raw)
                    mapped_input = {
                        "module": temp[0],
                        "output_name": temp[1],
                    }
                else:
                    raise ValueError(
                        f"Can't create child module '{module_id}': invalid type '{type(mapped_input_raw)}' for input '{name}'"
                    )

                # Now we have a dictionary, we need to augment it with defaults if necessary:
                #  - if no 'value_name' key is present, the input name will be used
                #  - if not 'module' key is present, the workflow will be connected to this input, not another module
                if mapped_input.get("module", None) is None:

                    workflow_input_name = mapped_input.get("workflow_input", None)

                    assert workflow_input_name is not None
                    value_name = mapped_input.get("output_name", None)

                    if value_name:
                        raise ValueError(
                            f"Input map in workflow '{self.id}' for item '{name}' has no 'module' key, but 'output_name', this is not allowed: {mapped_input}"
                        )

                    if workflow_input_name in self._workflow_inputs.keys():
                        raise ValueError(
                            f"Can't create child module '{module_id}': duplicate workflow input name '{workflow_input_name}' -- {mapped_input}"
                        )

                    wi = ValueLocation(
                        module=self,
                        value_name=workflow_input_name,
                        direction=ValueLocationType.input,
                    )
                    module_full_input_map[name] = wi
                    vl = ValueLocation(
                        module=module_obj,
                        value_name=name,
                        direction=ValueLocationType.input,
                    )
                    if wi in self._workflow_inputs.keys():
                        raise Exception(
                            f"Duplicate input name for workflow: {wi.value_name}"
                        )
                    self._workflow_inputs[wi] = vl
                    # all_outputs_map.setdefault(self.id, {})[workflow_input_name] = vl
                    self.data_flow_graph.add_edge(wi, vl)
                    # self.data_flow_graph.add_edge(self, wi)
                    self.data_flow_graph.add_edge(vl, module_obj)
                else:

                    workflow_input_name = mapped_input.get("workflow_input", None)

                    if workflow_input_name:
                        raise ValueError(
                            f"Input map in workflow '{self.id}' for item '{name}' contains 'module' key, but also 'workflow_input', this is not allowed: {mapped_input}"
                        )

                    value_name = mapped_input.get("output_name", None)

                    assert value_name is not None

                    # TODO: check format of mapped_input
                    o1 = ValueLocation(
                        module=self.get_module(mapped_input["module"]),
                        value_name=value_name,
                        direction=ValueLocationType.output,
                    )
                    module_full_input_map[name] = o1
                    i1 = ValueLocation(
                        module=module_obj,
                        value_name=name,
                        direction=ValueLocationType.input,
                    )

                    self.data_flow_graph.add_edge(o1.module, o1)
                    self.data_flow_graph.add_edge(o1, i1)
                    self.data_flow_graph.add_edge(i1, module_obj)

            self._module_details[module_id]["input_map"] = module_full_input_map

            input_locations: typing.Iterable[
                ValueLocation
            ] = module_full_input_map.values()

            # check if this module is connected to any other modules, if not, add an edge to the workflow itself
            # TODO: check if that is necessary
            if not input_locations or all(x.module == self for x in input_locations):
                self._execution_graph.add_edge(self, module_obj)

            # add all module connections for this modules input
            for loc in input_locations:
                if loc.module != self:
                    self._execution_graph.add_edge(loc.module, module_obj)

            # map outputs to workflow output, and subscribe to module output value changes
            for output_name in module_obj._state.outputs.trait_names():

                mo = ValueLocation(
                    module=module_obj,
                    value_name=output_name,
                    direction=ValueLocationType.output,
                )
                update_func = partial(self._module_output_updated, mo)
                module_obj._state.outputs.observe(update_func, names=output_name)

                output_details_raw = workflow_output_map.get(output_name, None)

                if output_details_raw is None:
                    # means there is no output to register for this output
                    continue
                elif isinstance(output_details_raw, str):

                    wo = ValueLocation(
                        module=self,
                        value_name=output_details_raw,
                        direction=ValueLocationType.output,
                    )
                    if wo in self._workflow_outputs.keys():
                        raise Exception(
                            f"Duplicate output name for workflow: {wo.value_name}"
                        )
                    self._workflow_outputs[wo] = mo

                    self.data_flow_graph.add_edge(module_obj, mo)
                    self.data_flow_graph.add_edge(mo, wo)
                else:
                    raise ValueError(
                        f"Can't add module '{module_id}': invalid type '{type(output_details_raw)}' for workflow output config -- {output_details_raw}"
                    )

        # calculate execution order
        path_lengths: typing.Dict[DharpaModule, int] = {}
        for m_d in self._module_details.values():

            _m: DharpaModule = m_d["module"]

            paths = list(nx.all_simple_paths(self.execution_graph, self, _m))
            max_steps = max(paths, key=lambda x: len(x))
            path_lengths[_m] = len(max_steps) - 1

        max_length = max(path_lengths.values())

        for i in range(1, max_length + 1):
            stage: typing.List[DharpaModule] = [
                m for m, length in path_lengths.items() if length == i
            ]
            self._execution_stages.append(stage)
            for _mod in stage:
                self._module_details[_mod.id]["processing_stage"] = i

        return config

    @property
    def execution_graph(self) -> nx.DiGraph:

        return self._execution_graph

    @property
    def data_flow_graph(self) -> nx.DiGraph:

        return self._data_flow_graph

    @property
    def execution_stages(self) -> typing.Iterable[typing.Iterable[DharpaModule]]:

        return self._execution_stages

    def _create_inputs(self, **config) -> HasTraits:

        traits = {}

        for workflow_input, module_input in self._workflow_inputs.items():

            assert module_input.direction == ValueLocationType.input

            m: DharpaModule = module_input.module
            trait_name = module_input.value_name
            trait = m._state.inputs.traits().get(trait_name)

            traits[workflow_input.value_name] = copy.deepcopy(trait)

        # dynamically create a new class that inherents from 'HasTraits'
        inputs_cls = type(
            f"WorkflowInputValues{to_camel_case(self.id, capitalize=True)}",
            (HasTraits,),
            traits,
        )

        inputs: HasTraits = inputs_cls()

        for workflow_input in self._workflow_inputs.keys():
            _m: DharpaModule = workflow_input.module
            assert _m == self

            func = partial(self._workflow_input_updated, workflow_input)
            inputs.observe(func, names=workflow_input.value_name)

        return inputs

    def _create_outputs(self, **config) -> HasTraits:

        traits = {}

        for workflow_output, module_output in self._workflow_outputs.items():

            assert module_output.direction == ValueLocationType.output

            module = module_output.module
            output_name = module_output.value_name
            trait = module._state.outputs.traits().get(output_name)
            traits[workflow_output.value_name] = copy.deepcopy(trait)

        outputs_cls = type(
            f"WorkflowOutputValues{to_camel_case(self.id, capitalize=True)}",
            (HasTraits,),
            traits,
        )
        return outputs_cls()

    # def get_input_location(self, value_name: str) -> ValueLocation:
    #
    #     return self._workflow_inputs[value_name]
    #
    # def get_output_location(self, value_name: str) -> ValueLocation:
    #
    #     return self._workflow_outputs[value_name]

    @property
    def modules(self) -> typing.Mapping[str, DharpaModule]:
        return {
            m_name: m_details["module"]
            for m_name, m_details in self._module_details.items()
        }

    def get_module(self, id: str) -> DharpaModule:

        md = self._module_details.get(id, None)
        if md is None:
            raise Exception(f"No module '{id}' in workflow '{self.id}'.")

        return md["module"]

    @property
    def module_ids(self) -> typing.Iterable[str]:

        return self._module_details.keys()

    def _process(self, **inputs) -> Mapping[str, typing.Any]:

        modules_executed: typing.Set[DharpaModule] = set()

        for i, modules_to_execute in enumerate(self._execution_stages):

            # print(f"Executing level: {i+1}")
            for m in modules_to_execute:
                # print(f"Executing: {m}")
                with m._state.outputs.hold_trait_notifications():
                    m.process()

            modules_executed.update(modules_to_execute)

        stale = self._is_stale()
        assert not stale

        self._state.busy = False
        # since we already updated the workflow outputs via the event system, we can skip the parent output
        # update mechanism here
        return None  # type: ignore

    # def add_module(self, module: DharpaModule):
    #
    #     if self._state.initialized:
    #         raise Exception(f"Can't add module '{module.id}': workflow already initialized")
    #     self.modules.append(module)
    #     self._state.stale = True
    #
    # def add_modules(self, *modules: DharpaModule):
    #
    #     for module in modules:
    #         self.add_module(module)
    #
    # def get_module(self, module_id: str) -> Optional[DharpaModule]:
    #
    #     result = None
    #     for m in self.modules:
    #         if m.id == module_id:
    #             result = m
    #             break
    #
    #     if result is None:
    #         raise Exception(f"Worfklow does not have module with id {module_id}.")
    #     return result

    @property
    def current_state(self):

        result = {"modules": {}}
        for module_id, module in self.modules.items():
            result["modules"][module_id] = module.current_state
        result["stale"] = self._state.stale
        return result

    @property
    def current_structure(self) -> typing.List[Mapping[str, typing.Any]]:

        result: typing.List[Mapping[str, typing.Any]] = []
        for module_details in self._module_details.values():
            module = module_details["module"]
            processing_stage = module_details["processing_stage"]
            is_workflow = isinstance(module, DharpaWorkflow) or issubclass(
                module.__class__, DharpaWorkflow
            )
            module_dict = {
                "module_id": module.id,
                "processing_stage": processing_stage,
                "module_type": module.__class__._module_name,
                "stale": module.stale,
                "busy": module.busy,
                "is_workflow": is_workflow,
            }
            if is_workflow:
                inner_workflow = module.current_structure
                module_dict["inner_structure"] = inner_workflow
            input_map = module_details["input_map"]
            module_dict["inputs"] = {}
            for input_name, target in input_map.items():
                if target.module == self:
                    module_dict["inputs"][input_name] = {"user_input": True}
                else:
                    target_module_id = target.module.id
                    target_value_name = target.value_name
                    module_dict["inputs"][input_name] = {
                        "module_id": target_module_id,
                        "output_name": target_value_name,
                        "user_input": False,
                    }
            module_dict["output_names"] = list(module.outputs.trait_names())

            result.append(module_dict)

        return result

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id='{self.id}' input_names={self._state.inputs.trait_names()} output_names={self._state.outputs.trait_names()}) modules={self.modules} config={self._config_raw}"

    def __str__(self):

        return f"workflow: '{self.id}'"
