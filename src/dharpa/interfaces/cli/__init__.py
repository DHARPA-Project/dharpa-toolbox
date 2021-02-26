# -*- coding: utf-8 -*-
import asyncclick as click
import dharpa
import zmq
from asciinet import graph_to_ascii
from dharpa.processing.executors import AsyncProcessor, ThreadPoolProcessor
from dharpa.workflows.events import ModuleEvent, ModuleEventType


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


@click.group()
async def cli():
    pass


@cli.group(name="execute")
async def execute():
    pass


@execute.command()
async def test():

    executor = AsyncProcessor()
    executor = ThreadPoolProcessor()

    # from dharpa.data.core import DataType
    from dharpa.workflows.workflow import DharpaWorkflow

    # find_all_processing_module_classes()
    # dw: DharpaWorkflow = DharpaWorkflow.from_file("tests/workflows/logic_3.yaml")

    # dw: DharpaWorkflow = DharpaWorkflow.from_file("/home/markus/projects/dharpa/dharpa-toolbox/src/dharpa/resources/workflows/logic_gates/xor.json")

    dw: DharpaWorkflow = dharpa.create_workflow("xor")
    print(dw)

    # wf: AssembledWorkflowBatch = dw.create_assembled_workflow()

    # thread = Thread(target=wf.listen)
    # thread.start()
    # thread.join()

    # wf.listen()

    dw.inputs.a = False
    dw.inputs.b = True
    # dw.inputs.and_1_1__b = True
    # dw.inputs.and_1_2__a = True
    # dw.inputs.and_1_2__b = True

    await dw.process(executor=executor)
    # await dw.process()
    # dw.inputs.and_2__b = False
    # dw.inputs.and_2__b = True
    # dw.process()

    print(dw.outputs.ALL)
    print(dw.state)

    # print(dw.doc)

    #
    graph = dw.structure.data_flow_graph
    print(graph_to_ascii(graph))
    #
    graph = dw.structure.execution_graph
    print(graph_to_ascii(graph))

    # graph = dw.structure.data_flow_graph

    # from grandalf.utils.nx import convert_nextworkx_graph_to_grandalf
    #
    # g = convert_nextworkx_graph_to_grandalf(graph)
    # sug = SugiyamaLayout(g)
    # sug.init_all()
    # sug.draw()


@execute.command()
def input_values():

    zmq_context: zmq.Context = zmq.Context.instance()
    module_event_socket: zmq.Socket = zmq_context.socket(zmq.PUSH)
    module_event_socket.connect("tcp://localhost:5555")

    ev = ModuleEvent(
        event_type=ModuleEventType.set_input,
        module_id="workflow",
        input_name="and_1__a",
        value=True,
    )
    module_event_socket.send_json(ev.to_dict())
    ev = ModuleEvent(
        event_type=ModuleEventType.set_input,
        module_id="workflow",
        input_name="and_1__b",
        value=True,
    )
    module_event_socket.send_json(ev.to_dict())


# req = typer.Typer()
# app.add_typer(req, name="req")
# resp = typer.Typer()
# app.add_typer(resp, name="resp")
#
# @req.command()
# def start():
#
#     port = "5556"
#     context = zmq.Context()
#     socket = context.socket(zmq.PAIR)
#     socket.bind("tcp://*:%s" % port)
#
#     i = 0
#     while True:
#         socket.send_string(f"Server message to client {i}")
#         socket.send_string(f"Server message to client {i}")
#         i = i + 1
#         msg = socket.recv()
#         print(msg)
#         time.sleep(1)
#
# @resp.command()
# def start():
#     port = "5556"
#     context = zmq.Context()
#     socket = context.socket(zmq.PAIR)
#     socket.connect("tcp://localhost:%s" % port)
#
#     i = 0
#     while True:
#         msg = socket.recv()
#         print(msg)
#         socket.send_string(f"client message to server {i}")
#         i = i + 1
#         socket.send_string(f"client message to server {i}")
#         i = i + 1
#         time.sleep(1)


# exec_typer = create_typers_from_modules()
# app.add_typer(exec_typer, name="run-module")
# app.add_typer(desc_typer, name="describe-processing")


def main():
    cli()


if __name__ == "__main__":
    main()
