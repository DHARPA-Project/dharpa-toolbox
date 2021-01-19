# -*- coding: utf-8 -*-
import typer
from dharpa_toolbox.modules.utils import (
    create_module,
    list_available_module_names,
    load_workflows,
)
from dharpa_toolbox.rendering.cli import create_typers_from_modules
from dharpa_toolbox.types.utils import get_input_python_types
from rich import print


app = typer.Typer()

workflow_descriptions_folder = (
    "/home/markus/projects/dharpa/dharpa-toolbox/dev/workflows"
)
load_workflows(workflow_descriptions_folder)


@app.command()
def list_modules():
    module_names = list_available_module_names()

    for m in module_names:
        if m == "dharpa_workflow":
            continue
        print(m)


@app.command()
def test():

    module_name = "corpus_processing"
    module_obj = create_module(module_name)

    import pp

    pp(module_obj.__dict__)

    types = get_input_python_types(module_obj)
    print(types)


exec_typer = create_typers_from_modules()
app.add_typer(exec_typer, name="run-module")
# app.add_typer(desc_typer, name="describe-modules")


def main():
    app()


if __name__ == "__main__":
    main()
