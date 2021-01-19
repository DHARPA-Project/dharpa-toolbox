# -*- coding: utf-8 -*-
import typer
from dharpa_toolbox.modules.utils import list_available_module_names, load_workflows
from dharpa_toolbox.rendering.cli import create_typers_from_modules
from dharpa_toolbox.rendering.jupyter.utils import find_all_item_widget_classes
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

    classes = find_all_item_widget_classes()
    print(classes)


exec_typer = create_typers_from_modules()
app.add_typer(exec_typer, name="run-module")
# app.add_typer(desc_typer, name="describe-modules")


def main():
    app()


if __name__ == "__main__":
    main()
