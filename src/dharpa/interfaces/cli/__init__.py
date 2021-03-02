# -*- coding: utf-8 -*-
import typing

import asyncclick as click
import dharpa
from dharpa.models import ModuleState
from dharpa.processing.processing_module import (
    ProcessingModule,
    get_doc_from_module_class,
)
from dharpa.utils import get_data_from_file
from dharpa.workflows.workflow import DharpaWorkflow, WorkflowProcessingModule
from rich import print as rich_print


# workflow_descriptions_folder = (
#     "/home/markus/projects/dharpa/dharpa-toolbox/dev/workflows"
# )
# load_workflows(workflow_descriptions_folder)


@click.group()
async def cli():
    pass


@cli.group(name="module")
async def module():
    pass


@module.group()
def run():
    pass


@module.group()
def json_state():
    pass


for name in dharpa.DHARPA_MODULES.all_names:

    short_help = f"execute module '{name}'"

    @run.command(
        name=name,
        short_help=short_help,
        context_settings=dict(
            ignore_unknown_options=True,
        ),
    )
    @click.argument("path_to_inputs", nargs=1, required=False)
    async def module_run_command(path_to_inputs, name=name):

        dw: DharpaWorkflow = dharpa.create_workflow(name)
        if path_to_inputs:
            inputs = get_data_from_file(path_to_inputs)
            dw.inputs = inputs

        if dw.state != ModuleState.STALE:
            await dw.process()
            print(dw.outputs.ALL)
        else:
            print("Not all inputs ready.")

    short_help = f"print the state module '{name}' as json"

    @json_state.command(  # noqa
        name=name,
        short_help=short_help,
        context_settings=dict(
            ignore_unknown_options=True,
        ),
    )
    @click.argument("path_to_inputs", nargs=1, required=False)
    async def module_run_command(path_to_inputs, name=name):

        dw: DharpaWorkflow = dharpa.create_workflow(name)
        if path_to_inputs:
            inputs = get_data_from_file(path_to_inputs)
            dw.inputs = inputs

        if dw.state != ModuleState.STALE:
            await dw.process()

        json_str = dw.to_json(indent=2)
        print(json_str)


@module.command()
@click.argument("module_names", nargs=-1)
def info(module_names):

    for module_name in module_names:

        m_cls = dharpa.DHARPA_MODULES.get(module_name)
        m = m_cls._processing_step_config_cls

        rich_print(f"- [i]module[/i]: [b]{module_name}[/b]")
        rich_print(f"  [i]doc[/i]: {get_doc_from_module_class(m_cls)}")
        is_pipeline = issubclass(m_cls, WorkflowProcessingModule)
        rich_print(f"  [i]is_pipeline[/i]: {is_pipeline}")

        rich_print("  [i]configuration options:[/i]")
        schema = m.schema()
        for name in sorted(schema["properties"].keys()):
            prop = schema["properties"][name]
            desc = prop.get("description", None)
            if desc:
                n_str = f"    [i]{name}[/i]: {desc}"
            else:
                n_str = f"    [i]{name}[/i]:"
            rich_print(n_str)
            rich_print(f"      [i]type[/i]: {prop['type']}")
            if prop.get("default", None) is not None:
                rich_print(f"      [i]required[/i]: no (default: {prop['default']})")
            else:
                rich_print("      [i]required[/i]: yes")


@module.command()
@click.option("--details", "-d", is_flag=True, help="whether to display module details")
def list(details: bool = False):

    for name in dharpa.DHARPA_MODULES.all_names:
        if name == "workflow":
            continue
        m_cls: typing.Optional[
            typing.Type[ProcessingModule]
        ] = dharpa.DHARPA_MODULES.get(name)
        if m_cls is None:
            raise Exception(f"No module registered for: {name}")
        m = m_cls._processing_step_config_cls  # type: ignore
        rich_print(f"- [i]module[/i]: [b]{name}[/b]")
        rich_print(f"  [i]doc[/i]: {get_doc_from_module_class(m_cls)}")
        is_pipeline = issubclass(m_cls, WorkflowProcessingModule)
        rich_print(f"  [i]is_pipeline[/i]: {is_pipeline}")
        if details:
            rich_print("  [i]configuration options:[/i]")
            schema = m.schema()
            for name in sorted(schema["properties"].keys()):
                prop = schema["properties"][name]
                desc = prop.get("description", None)
                if desc:
                    n_str = f"    [i]{name}[/i]: {desc}"
                else:
                    n_str = f"    [i]{name}[/i]:"
                rich_print(n_str)
                rich_print(f"      [i]type[/i]: {prop['type']}")
                if prop.get("default", None) is not None:
                    rich_print(
                        f"      [i]required[/i]: no (default: {prop['default']})"
                    )
                else:
                    rich_print("      [i]required[/i]: yes")


def main():
    cli()


if __name__ == "__main__":
    main()
