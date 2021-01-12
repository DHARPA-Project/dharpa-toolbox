# -*- coding: utf-8 -*-

__all__ = [
    "TextPreprocessSettingsModule",
    "TextPreprocessingModule",
    "TextCorpusValue",
    "TextCorpusInputValue",
    "TokenizeTextModule",
    "TextCorpusProcessingModule",
    "LowercaseTextModule",
    "RemoveStopwordsModule",
    "CorpusProcessingWorkflow",
]

# Cell

import typing
from abc import abstractmethod

import nltk
import traitlets
from dharpa_toolbox.modules.workflows import DharpaWorkflow
from traitlets import Any, Bool, Dict, HasTraits, Instance

from .core import DharpaModule
from .files import DharpaFiles, TextCorpus


class TextPreprocessSettingsModule(DharpaModule):

    _module_name = "text_preprocess_settings"

    def _create_inputs(self, **config) -> HasTraits:
        class TextPreprocessingInput(HasTraits):
            file_set = Instance(klass=DharpaFiles, allow_none=True)
            lowercase = Bool(default_value=True)

        return TextPreprocessingInput()

    def _create_outputs(self, **config) -> HasTraits:
        class TextPreprocessingSettings(HasTraits):
            settings = Dict(allow_none=True)

        return TextPreprocessingSettings()

    def _process(self, **inputs) -> typing.Mapping[str, typing.Any]:

        return {"settings": {"lowercase": inputs["lowercase"]}}


class TextPreprocessingModule(DharpaModule):

    _module_name = "text_preprocessing"

    def _create_inputs(self, **config) -> HasTraits:
        class TextPreprocessingInput(HasTraits):
            file_set = Instance(klass=DharpaFiles, allow_none=True)
            settings = Dict(allow_none=True)

        return TextPreprocessingInput()

    def _create_outputs(self, **config):
        class TextPreprocessingOutput(HasTraits):
            preprocessed_text = Dict(allow_none=True)

        return TextPreprocessingOutput()

    def _process(self, **inputs) -> typing.Mapping[str, typing.Any]:

        result = {}
        file_set: DharpaFiles = inputs["file_set"]
        if file_set is None:
            file_set = DharpaFiles()

        for f in file_set.files:
            result[f.name] = f.content.lower()

        return result


class TextCorpusValue(HasTraits):

    text_corpus = Instance(klass=TextCorpus)


class TextCorpusInputValue(TextCorpusValue):

    enabled = Bool(default_value=True)


class TokenizeTextModule(DharpaModule):

    _module_name = "tokenize"

    def _create_inputs(self, **config) -> HasTraits:
        class TokenizeTextInput(HasTraits):
            file_set = Instance(klass=DharpaFiles)

        return TokenizeTextInput()

    def _create_outputs(self, **config) -> HasTraits:

        return TextCorpusValue()

    def _process(self, **inputs) -> typing.Mapping[str, typing.Any]:

        result = {}

        corpus: TextCorpus = inputs.pop("text_corpus")

        for id, text in corpus.corpus().items():

            r = nltk.wordpunct_tokenize(text)
            # TODO: check if iterable of strings
            if r:
                result[id] = r

        return result


class TextCorpusProcessingModule(DharpaModule):
    @abstractmethod
    def _process_tokens(
        self, token_set: typing.List[str], config: typing.Mapping[str, Any]
    ) -> typing.List[str]:
        pass

    def _create_inputs(self, **config) -> HasTraits:

        return TextCorpusInputValue()

    def _create_outputs(self, **config) -> HasTraits:

        return TextCorpusValue()

    def _process(self, **inputs) -> typing.Mapping[str, typing.Any]:

        raise NotImplementedError()

        # result = {}
        #
        # config = copy.copy(inputs)
        # token_sets = config.pop("token_sets")
        #
        # for id, token_set in token_sets.items():
        #
        #     raise NotImplementedError()
        #
        #     # r = self._process_text(token_set=token_set, config=config)
        #     # if r:
        #     #     result[id] = r
        #
        # return {"token_sets": result}


class LowercaseTextModule(TextCorpusProcessingModule):

    _module_name = "lowercase"

    def _process_tokens(
        self, token_set: typing.List[str], config: typing.Mapping[str, Any]
    ) -> typing.List[str]:

        return [x.lower() for x in token_set]


class RemoveStopwordsModule(TextCorpusProcessingModule):

    _module_name = "remove_stopwords"

    def _create_inputs(self, **config) -> HasTraits:
        class RemoveStopwordsInput(TextCorpusInputValue):
            stopwords = traitlets.List()

        return RemoveStopwordsInput()

    def _process_tokens(
        self, token_set: typing.List[str], config: typing.Mapping[str, Any]
    ) -> typing.List[str]:

        stopwords = config["stopwords"]

        return [x for x in token_set if x not in stopwords]


class CorpusProcessingWorkflow(DharpaWorkflow):

    _module_name = "corpus_processing"

    def __init__(self, **config):

        modules = [
            {
                "type": "tokenize",
                "id": "tokenize_corpus",
                "input_map": {
                    "file_set": {"value_name": "file_set"},
                },
            },
            {
                "type": "lowercase",
                "id": "lowercase_corpus",
                "input_map": {
                    "text_corpus": {
                        "module": "tokenize_corpus",
                        "value_name": "text_corpus",
                    },
                    "enabled": {"value_name": "enable_lowercase"},
                },
            },
            {
                "type": "remove_stopwords",
                "id": "remove_stopwords_from_corpus",
                "input_map": {
                    "text_corpus": "lowercase_corpus",
                    "stopwords": {"value_name": "stopwords"},
                    "enabled": {"value_name": "enable_stopwords_removal"},
                },
                "workflow_output": {"text_corpus": "processed_text_corpus"},
            },
        ]
        super().__init__(modules=modules, **config)
