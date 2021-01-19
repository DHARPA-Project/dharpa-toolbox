# -*- coding: utf-8 -*-
from dharpa_toolbox.modules.utils import load_workflows
from dharpa_toolbox.rendering.rest_api import create_routers_from_modules
from fastapi import FastAPI


# new_config = {
#     "modules": [
#         {
#             "type": "file_reader"
#         },
#         {
#             "type": "tokenize_workflow",
#             "input_map": {
#                 "tokenize_corpus__text_map": "file_reader.content_map"
#             },
#             "workflow_outputs": {
#                 "processed_text_corpus": "processed_text_corpus"
#             }
#         }
#     ]
# }
#
# base_path = Path("/home/markus/projects/dharpa/dharpa-toolbox/dev")
#
# config_path = base_path / "corpus_processing.yaml"
# print_module_desc("tokenize_corpus", "lowercase_corpus", "remove_stopwords_from_corpus")
#
# workflow_config = get_data_from_file(config_path)
#
# class TokenizeWorkflow(DharpaWorkflow):
#
#     _module_name = "tokenize_workflow"
#
#     def __init__(self, **config):
#
#         config.update(workflow_config)
#
#         super().__init__(**config)
#
# new_workflow = DharpaWorkflow(**new_config)
# print_module_desc(new_workflow)

workflow_descriptions_folder = (
    "/home/markus/projects/dharpa/dharpa-toolbox/dev/workflows"
)
load_workflows(workflow_descriptions_folder)


app = FastAPI()

module_router, workflow_router = create_routers_from_modules()

app.include_router(module_router, prefix="/modules")
app.include_router(workflow_router, prefix="/workflows")
