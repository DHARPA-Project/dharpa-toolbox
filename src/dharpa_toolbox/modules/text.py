# -*- coding: utf-8 -*-

# Cell
import copy
import typing
from abc import abstractmethod

import nltk
import traitlets
from traitlets import Any, Bool, Dict, HasTraits, List, Unicode

from .core import DharpaModule


class TokenizedTextValue(HasTraits):

    tokenized_text = Dict(key_trait=Unicode(), value_trait=List(trait=Unicode()))


class PreprocessorInputValue(TokenizedTextValue):

    enabled = Bool(default_value=True)


class TokenizeCorpusModule(DharpaModule):
    """Tokenize a text collection.

    The 'text_map' input is a dict with the id of a text as the key, and the text (as string) as the value.
    """

    _module_name = "tokenize_corpus"

    def _create_inputs(self, **config) -> HasTraits:
        class TokenizeTextInputFiles(HasTraits):
            text_map = Dict(key_trait=Unicode(), value_trait=Unicode())

        return TokenizeTextInputFiles()

    def _create_outputs(self, **config) -> HasTraits:

        return TokenizedTextValue()

    def _process(self, **inputs) -> typing.Mapping[str, typing.Any]:

        result = {}

        corpus: typing.Mapping[str, str] = inputs["text_map"]

        for id, text in corpus.items():

            r = nltk.wordpunct_tokenize(text)
            # TODO: check if iterable of strings
            if r:
                result[id] = r

        return {"tokenized_text": result}


class TextPreprocessingModule(DharpaModule):
    @abstractmethod
    def _process_tokens(
        self, token_set: typing.List[str], config: typing.Mapping[str, Any]
    ) -> typing.List[str]:
        pass

    def _create_inputs(self, **config) -> HasTraits:

        return PreprocessorInputValue()

    def _create_outputs(self, **config) -> HasTraits:

        return TokenizedTextValue()

    def _process(self, **inputs) -> typing.Mapping[str, typing.Any]:

        result = {}

        config = copy.copy(inputs)
        token_sets = config.pop("tokenized_text")
        enabled = config.pop("enabled")

        if not enabled:
            return {"tokenized_text": token_sets}

        for id, token_set in token_sets.items():

            r = self._process_tokens(token_set=token_set, config=config)
            if r:
                result[id] = r

        return {"tokenized_text": result}


class LowercaseTextModule(TextPreprocessingModule):
    """Lowercase every word in a corpus.

    The 'tokenized_text' input is a dictionary with an id of a text as key, and the tokenized text itself (as list of strings) as value.
    """

    _module_name = "lowercase_corpus"

    def _process_tokens(
        self, token_set: typing.List[str], config: typing.Mapping[str, Any]
    ) -> typing.List[str]:

        return [x.lower() for x in token_set]


class RemoveStopwordsModule(TextPreprocessingModule):
    """Remove stopwords from a corpus.

    The 'tokenized_text' input is a dictionary with an id of a text as key, and the tokenized text itself (as list of strings) as value.
    """

    _module_name = "remove_stopwords_from_corpus"

    def _create_inputs(self, **config) -> HasTraits:
        class RemoveStopwordsInput(PreprocessorInputValue):
            stopwords_list = traitlets.List(
                default_value=[], trait=Unicode(allow_none=False)
            )

        return RemoveStopwordsInput()

    def _process_tokens(
        self, token_set: typing.List[str], config: typing.Mapping[str, Any]
    ) -> typing.List[str]:

        stopwords = config["stopwords_list"]

        return [x for x in token_set if x not in stopwords]
