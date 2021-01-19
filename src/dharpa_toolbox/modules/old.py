# -*- coding: utf-8 -*-
# class TextCorpus(object):
# def __init__(self, file_set: DharpaFiles):
#
# self._file_set: DharpaFiles = file_set
# self._corpus: typing.Mapping[str, typing.Union[str, typing.List[str]]] = None  # type: ignore
#
# def file_set(self) -> DharpaFiles:
# return self._file_set
#
# def corpus(self) -> typing.Mapping[str, str]:
#
# if self._corpus is not None:
# return self._corpus
#
# self._corpus = {}
# for f in self._file_set.files:
# text = f.content.decode("utf-8")
# self._corpus[f.name] = text
#
# return self._corpus
#
#
# class TextCorpusValue(HasTraits):
#
# text_corpus = Instance(klass=TextCorpus)
#
#
# class CorpusFromFiles(DharpaModule):
#
# _module_name = "corpus_from_files"
#
# def _create_inputs(self, **config) -> HasTraits:
#
# return FileSetValue()
#
# def _create_outputs(self, **config) -> HasTraits:
#
# return TextCorpusValue()
#
# def _process(self, **inputs) -> typing.Mapping[str, typing.Any]:
#
# file_set: DharpaFiles = inputs["file_set"]
# result = TextCorpus(file_set=file_set)
# return {"text_corpus": result}
from dharpa_toolbox.modules.workflows import DharpaWorkflow


class CorpusProcessingWorkflow(DharpaWorkflow):

    _module_name = "corpus_processing"

    def __init__(self, **config):

        modules = [
            {
                "type": "tokenize",
                "id": "tokenize_corpus",
                "input_map": {
                    "file_set": "__workflow_input__.file_set",
                },
            },
            {
                "type": "lowercase",
                "id": "lowercase_corpus",
                "input_map": {
                    "tokenized_text": "tokenize_corpus.tokenized_text",
                    "enabled": "__workflow_input__.enable_lowercase",
                },
                "workflow_outputs": {"tokenized_text": "tokenized_text_lowercase"},
            },
            {
                "type": "remove_stopwords",
                "id": "remove_stopwords_from_corpus",
                "input_map": {
                    "tokenized_text": "lowercase_corpus.tokenized_text",
                    "stopwords_list": "__workflow_input__.stopwords_list",
                    "enabled": "__workflow_input__.remove_stopwords",
                },
                "workflow_outputs": {"tokenized_text": "processed_text_corpus"},
            },
        ]
        super().__init__(modules=modules, **config)
