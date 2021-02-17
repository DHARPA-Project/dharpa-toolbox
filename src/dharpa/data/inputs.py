# -*- coding: utf-8 -*-
# HASHED_SCHEMAS: Dict[str, Union[Type[BaseModel], Exception]] = {}
#
# def create_data_model(**schema: typing.Any) -> Type[BaseModel]:
#     """Dynamically create a Python class from a schema.
#     """
#
#     _hashes = deepdiff.DeepHash(schema)
#     schema_hash = _hashes[schema]
#
#     if schema_hash in HASHED_SCHEMAS.keys():
#         result = HASHED_SCHEMAS[schema_hash]
#         if isinstance(result, Exception):
#             raise result
#         else:
#             return result
#
#     try:
#         class ExampleModel(BaseModel):
#             x: str
#             y: str
#         result = ExampleModel
#         HASHED_SCHEMAS[schema_hash] = result
#         return result
#     except Exception as e:
#         HASHED_SCHEMAS[schema_hash] = e
#         raise e
