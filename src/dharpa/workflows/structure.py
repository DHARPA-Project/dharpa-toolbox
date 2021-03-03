# -*- coding: utf-8 -*-
import networkx as nx
import typing
from functools import lru_cache

from dharpa.data.core import DataSchema
from dharpa.models import ChildModuleDetails, WorkflowStructureDetails
from dharpa.workflows.modules import WorkflowModule
from dharpa.workflows.utils import create_workflow_modules


class DataLink(object):
    def __init__(self, value_name: str, schema: DataSchema):
        self._value_name = value_name
        self._schema: DataSchema = schema

    @property
    def value_name(self) -> str:
        return self._value_name

    @property
    def schema(self) -> DataSchema:
        return self._schema


class ModuleLink(DataLink):
    def __init__(self, module_id: str, value_name: str, schema: DataSchema):

        super().__init__(value_name=value_name, schema=schema)
        self._module_id = module_id

    @property
    def module_id(self) -> str:
        return self._module_id

    @property
    def name(self) -> str:
        return f"{self.module_id}.{self.value_name}"


class ModuleInputLink(ModuleLink):

    link_type: str = "module_input"

    def __init__(
        self,
        module_id: str,
        value_name: str,
        schema: DataSchema,
        connected_item: typing.Union["WorkflowInputLink", "ModuleOutputLink"],
    ):

        super().__init__(module_id=module_id, value_name=value_name, schema=schema)
        self._connected_item: typing.Union[
            WorkflowInputLink, ModuleOutputLink
        ] = connected_item

    @property
    def connected_item(self) -> typing.Union["WorkflowInputLink", "ModuleOutputLink"]:
        return self._connected_item

    def __repr__(self):
        return (
            f"ModuleInputLink(module='{self.module_id}' input_name='{self.value_name}')"
        )


class ModuleOutputLink(ModuleLink):

    link_type: str = "module_output"

    def __init__(self, module_id: str, value_name: str, schema: DataSchema):
        super().__init__(module_id=module_id, value_name=value_name, schema=schema)
        self._connected_inputs: typing.List[ModuleInputLink] = []
        self._connected_workflow_output: typing.Optional[WorkflowOutputLink] = None

    @property
    def workflow_output(self) -> typing.Optional["WorkflowOutputLink"]:
        return self._connected_workflow_output

    @property
    def connected_inputs(self) -> typing.Iterable["ModuleInputLink"]:
        return self._connected_inputs

    def connect_target(
        self, target: typing.Union[ModuleInputLink, "WorkflowOutputLink"]
    ):

        if isinstance(target, ModuleInputLink):
            self._connected_inputs.append(target)
        elif isinstance(target, WorkflowOutputLink):
            if self._connected_workflow_output is not None:
                raise Exception(f"Workflow output already set for: {self}")
            self._connected_workflow_output = target
        else:
            raise TypeError(f"Invalid target type: {type(target)}")

    def __repr__(self):
        return f"ModuleOutputLink(module='{self.module_id}' output_name='{self.value_name}')"


class WorkflowInputLink(DataLink):

    link_type: str = "workflow_input"

    def __init__(
        self,
        value_name: str,
        schema: DataSchema,
        connected_input: typing.Optional[ModuleInputLink] = None,
    ):
        super().__init__(value_name=value_name, schema=schema)
        self._connected_input: typing.Optional[ModuleInputLink] = connected_input

    @property
    def connected_input(self) -> ModuleInputLink:

        if self._connected_input is None:
            raise Exception(f"Connected input not set yet for '{self}'")
        return self._connected_input

    @connected_input.setter
    def connected_input(self, connected_input: ModuleInputLink):
        self._connected_input = connected_input

    @property
    def name(self):
        return self.value_name

    def __repr__(self):
        return f"WorkflowInputLink(input_name='{self.value_name}')"


class WorkflowOutputLink(DataLink):

    link_type: str = "workflow_output"

    def __init__(
        self, value_name: str, schema: DataSchema, connected_output: ModuleOutputLink
    ):
        super().__init__(value_name=value_name, schema=schema)
        self._connected_output: ModuleOutputLink = connected_output

    @property
    def connected_output(self) -> ModuleOutputLink:
        return self._connected_output

    @property
    def name(self):
        return self.value_name

    def __repr__(self):
        return f"WorkflowOutputLink(output_name='{self.value_name}')"


class WorkflowStructure(object):
    def __init__(
        self,
        *modules: typing.Union[typing.Mapping, WorkflowModule],
        workflow_id: str,
        input_aliases: typing.Mapping[str, str] = None,
        output_aliases: typing.Mapping[str, str] = None,
        add_all_workflow_outputs: bool = False,
    ):

        self._workflow_id: str = workflow_id
        self._workflow_modules: typing.List[WorkflowModule] = create_workflow_modules(
            *modules, workflow_id=workflow_id, force_mappings=True
        )

        if input_aliases is None:
            input_aliases = {}
        self._input_aliases: typing.Mapping[str, str] = input_aliases
        if output_aliases is None:
            output_aliases = {}
        self._output_aliases: typing.Mapping[str, str] = output_aliases

        self._add_all_workflow_outputs: bool = add_all_workflow_outputs

        self._execution_graph: nx.DiGraph = None  # type: ignore
        self._data_flow_graph: nx.DiGraph = None  # type: ignore

        self._execution_stages: typing.List[typing.List[str]] = None  # type: ignore

        self._module_details: typing.Dict[str, typing.Any] = None  # type: ignore
        """Holds details about the (current) processing contained in this workflow."""

    @property
    def modules(self) -> typing.Iterable[WorkflowModule]:
        return self._workflow_modules

    @property
    def module_details(self) -> typing.Mapping[str, typing.Any]:

        if self._module_details is None:
            self._process_modules()
        return self._module_details

    def get_module(self, module_id: str) -> WorkflowModule:

        d = self.module_details.get(module_id, None)
        if d is None:
            raise Exception(f"No module with id: {module_id}")

        return d["workflow_module"]

    def get_module_inputs(self, module_id: str) -> typing.Iterable[ModuleInputLink]:

        d = self.module_details.get(module_id, None)
        if d is None:
            raise Exception(f"No module with id: {module_id}")

        return d["inputs"]

    def get_module_outputs(self, module_id: str) -> typing.Iterable[ModuleInputLink]:

        d = self.module_details.get(module_id, None)
        if d is None:
            raise Exception(f"No module with id: {module_id}")

        return d["outputs"]

    def get_module_details(self, module_id: str) -> typing.Mapping[str, typing.Any]:

        d = self.module_details.get(module_id, None)
        if d is None:
            raise Exception(f"No module with id: {module_id}")

        return d

    @property
    def execution_graph(self) -> nx.DiGraph:
        if self._execution_graph is None:
            self._process_modules()
        return self._execution_graph

    @property
    def data_flow_graph(self) -> nx.DiGraph:
        if self._data_flow_graph is None:
            self._process_modules()
        return self._data_flow_graph

    @property
    def execution_stages(self) -> typing.List[typing.List[str]]:
        if self._execution_stages is None:
            self._process_modules()
        return self._execution_stages

    @lru_cache()
    def _get_node_of_type(self, node_type: str):
        if self._execution_stages is None:
            self._process_modules()

        return [
            node
            for node, attr in self._data_flow_graph.nodes(data=True)
            if attr["type"] == node_type
        ]

    @property
    def workflow_inputs(self) -> typing.Dict[str, WorkflowInputLink]:
        return {
            node.name: node
            for node in self._get_node_of_type(node_type=WorkflowInputLink.link_type)
        }

    @property
    def workflow_outputs(self) -> typing.Dict[str, WorkflowOutputLink]:
        return {
            node.name: node
            for node in self._get_node_of_type(node_type=WorkflowOutputLink.link_type)
        }

    @property
    def module_inputs(self) -> typing.Dict[str, ModuleInputLink]:
        return {
            node.name: node
            for node in self._get_node_of_type(node_type=ModuleInputLink.link_type)
        }

    @property
    def module_outputs(self) -> typing.Dict[str, ModuleOutputLink]:
        return {
            node.name: node
            for node in self._get_node_of_type(node_type=ModuleOutputLink.link_type)
        }

    @property
    def workflow_input_schema(self) -> typing.Mapping[str, DataSchema]:

        return {
            input_name: w_in.schema for input_name, w_in in self.workflow_inputs.items()
        }

    @property
    def workflow_output_schema(self) -> typing.Mapping[str, DataSchema]:
        return {
            output_name: w_out.schema
            for output_name, w_out in self.workflow_outputs.items()
        }

    def _process_modules(self):
        """The core method of this class, it connects all the processing modules, their inputs and outputs."""

        module_details: typing.Dict[str, typing.Any] = {}
        execution_graph = nx.DiGraph()
        execution_graph.add_node("__root__")
        data_flow_graph = nx.DiGraph()
        execution_stages = []

        # temp variable, to hold all outputs
        outputs: typing.Dict[str, ModuleOutputLink] = {}

        # add all processing and module outputs first
        for workflow_module in self._workflow_modules:

            module_details[workflow_module.alias] = {
                "workflow_module": workflow_module,
                "outputs": {},
                "inputs": {},
            }

            data_flow_graph.add_node(workflow_module, type="module")

            for output_name, schema in workflow_module.output_schema.items():

                module_output = ModuleOutputLink(
                    module_id=workflow_module.alias,
                    value_name=output_name,
                    schema=schema,
                )
                module_details[workflow_module.alias]["outputs"][
                    output_name
                ] = module_output
                outputs[f"{workflow_module.alias}.{output_name}"] = module_output

                m_id = f"{workflow_module.alias}__{output_name}"
                if self._output_aliases:
                    if m_id in self._output_aliases.keys():
                        m_id = self._output_aliases[m_id]
                    else:
                        if not self._add_all_workflow_outputs:
                            # this output is not interesting for the workflow
                            m_id = None

                if m_id:
                    workflow_output = WorkflowOutputLink(
                        value_name=m_id,
                        connected_output=module_output,
                        schema=schema,
                    )
                    module_output.connect_target(workflow_output)
                    data_flow_graph.add_node(
                        workflow_output, type=WorkflowOutputLink.link_type
                    )
                    data_flow_graph.add_edge(module_output, workflow_output)

                data_flow_graph.add_edge(workflow_module, module_output)
                data_flow_graph.add_node(module_output, type=ModuleOutputLink.link_type)

        existing_input_links: typing.Dict = {}
        for workflow_module in self._workflow_modules:

            other_module_dependency: typing.Set = set()
            for input_name, schema in workflow_module.input_schema.items():
                link_workflow_input = False
                if input_name in workflow_module.input_connection_map.keys():
                    connected_output_data = workflow_module.input_connection_map[
                        input_name
                    ]
                    connected_data: ModuleOutputLink = outputs[
                        f"{connected_output_data['module_id']}.{connected_output_data['value_name']}"
                    ]
                    other_module_dependency.add(connected_data.module_id)
                else:
                    m_id = f"{workflow_module.alias}__{input_name}"
                    if self._input_aliases:
                        if m_id in self._input_aliases.keys():
                            m_id = self._input_aliases[m_id]

                    if m_id in existing_input_links.keys():
                        connected_data = existing_input_links[m_id]
                    else:
                        connected_data = WorkflowInputLink(
                            value_name=m_id, schema=schema
                        )
                        data_flow_graph.add_node(
                            connected_data, type=WorkflowInputLink.link_type
                        )
                    link_workflow_input = True

                input_link = ModuleInputLink(
                    module_id=workflow_module.alias,
                    value_name=input_name,
                    schema=schema,
                    connected_item=connected_data,
                )

                data_flow_graph.add_node(input_link, type=ModuleInputLink.link_type)

                if link_workflow_input:
                    connected_data.connected_input = input_link
                    data_flow_graph.add_edge(connected_data, input_link)
                    if connected_data.value_name not in existing_input_links.keys():
                        existing_input_links[connected_data.value_name] = connected_data
                else:
                    connected_data.connect_target(input_link)
                    data_flow_graph.add_edge(connected_data, input_link)

                module_details[workflow_module.alias]["inputs"][input_name] = input_link

                data_flow_graph.add_edge(input_link, workflow_module)

            if other_module_dependency:
                for module_id in other_module_dependency:
                    execution_graph.add_edge(module_id, workflow_module.alias)
            else:
                execution_graph.add_edge("__root__", workflow_module.alias)

        # calculate execution order
        path_lengths: typing.Dict[str, int] = {}

        for workflow_module in self._workflow_modules:

            module_id = workflow_module.alias

            paths = list(nx.all_simple_paths(execution_graph, "__root__", module_id))
            max_steps = max(paths, key=lambda x: len(x))
            path_lengths[module_id] = len(max_steps) - 1

        max_length = max(path_lengths.values())

        for i in range(1, max_length + 1):
            stage: typing.List[str] = [
                m for m, length in path_lengths.items() if length == i
            ]
            execution_stages.append(stage)
            for _mod_id in stage:
                module_details[_mod_id]["processing_stage"] = i
                module_details[_mod_id]["workflow_module"].execution_stage = i

        self._module_details = module_details
        self._execution_graph = execution_graph
        self._data_flow_graph = data_flow_graph
        self._execution_stages = execution_stages

        self._get_node_of_type.cache_clear()

    def to_details(self) -> WorkflowStructureDetails:

        modules = []
        workflow_inputs: typing.Dict[str, typing.List[str]] = {}
        workflow_outputs: typing.Dict[str, str] = {}

        for m_id, details in self.module_details.items():
            m_det = details["workflow_module"].to_details()

            input_connections = {}
            for k, v in details["inputs"].items():
                if v.connected_item.link_type == WorkflowInputLink.link_type:
                    input_connections[k] = f"__parent__.{v.connected_item.name}"
                    workflow_inputs.setdefault(v.connected_item.name, []).append(v.name)
                elif v.connected_item.link_type == ModuleOutputLink.link_type:
                    input_connections[k] = v.connected_item.name
                else:
                    raise TypeError(
                        f"Invalid connection type: {type(v.connected_item)}"
                    )

            output_connections: typing.Dict[str, typing.Any] = {}
            for k, v in details["outputs"].items():
                for connected_item in v.connected_inputs:
                    output_connections.setdefault(k, []).append(connected_item.name)
                if v.workflow_output:
                    output_connections.setdefault(k, []).append(
                        f"__parent__.{v.workflow_output.name}"
                    )
                    workflow_outputs[v.workflow_output.name] = v.name

            modules.append(
                ChildModuleDetails(
                    module=m_det,
                    input_connections=input_connections,
                    output_connections=output_connections,
                )
            )

        return WorkflowStructureDetails(
            workflow_id=self._workflow_id,
            modules=modules,
            workflow_input_connections=workflow_inputs,
            workflow_output_connections=workflow_outputs,
        )

    def to_dict(self) -> typing.Dict[str, typing.Any]:

        return self.to_details().dict()
