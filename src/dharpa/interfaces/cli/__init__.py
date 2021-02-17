# -*- coding: utf-8 -*-
import typer


app = typer.Typer()

# workflow_descriptions_folder = (
#     "/home/markus/projects/dharpa/dharpa-toolbox/dev/workflows"
# )
# load_workflows(workflow_descriptions_folder)


# @app.command()
# def list_modules():
#     module_names = list_available_module_names()
#
#     for m in module_names:
#         if m == "dharpa_workflow":
#             continue
#         print(m)


@app.command()
def test():

    # from dharpa.data.core import DataType
    from dharpa.utils import find_all_module_classes
    from dharpa.workflows.workflow import DharpaWorkflow

    find_all_module_classes()

    dw: DharpaWorkflow = DharpaWorkflow.from_file("tests/workflows/logic_2.yaml")

    # dw.inputs.and_1__a = True
    # dw.inputs.and_1__b = True
    # dw.inputs.and_2__b = True

    dw.process()
    dw.inputs.and_2__b = False
    dw.inputs.and_2__b = True
    dw.process()

    print(dw.outputs.ALL)
    print(dw.state)

    # graph = dw.structure.data_flow_graph

    # from grandalf.utils.nx import convert_nextworkx_graph_to_grandalf
    #
    # g = convert_nextworkx_graph_to_grandalf(graph)
    # sug = SugiyamaLayout(g)
    # sug.init_all()
    # sug.draw()


# exec_typer = create_typers_from_modules()
# app.add_typer(exec_typer, name="run-module")
# app.add_typer(desc_typer, name="describe-processing")


def main():
    app()


if __name__ == "__main__":
    main()
