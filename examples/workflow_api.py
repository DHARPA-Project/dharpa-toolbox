# -*- coding: utf-8 -*-
import os

from dharpa_toolbox.modules.utils import load_workflows
from dharpa_toolbox.rendering.rest_api import (
    create_doc_routers_from_modules,
    create_processing_routers_from_modules,
)
from fastapi import FastAPI


THIS_FOLDER = os.path.dirname(__file__)
workflow_descriptions_folder = os.path.join(THIS_FOLDER, "workflows")
load_workflows(workflow_descriptions_folder)


app = FastAPI()

module_router, workflow_router = create_processing_routers_from_modules()

app.include_router(module_router, prefix="/processing/modules")
app.include_router(workflow_router, prefix="/processing/workflows")

(
    nav_doc_router,
    doc_module_router,
    doc_workflow_router,
) = create_doc_routers_from_modules()

app.include_router(nav_doc_router, prefix="/ids")
app.include_router(doc_module_router, prefix="/doc/modules")
app.include_router(doc_workflow_router, prefix="/doc/workflows")
