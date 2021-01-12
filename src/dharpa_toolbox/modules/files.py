# -*- coding: utf-8 -*-

import collections
import os
import typing

import traitlets
from traitlets import Bytes, HasTraits, Instance, Integer, Unicode

from .core import DharpaModule


class DharpaFile(HasTraits):
    @classmethod
    def create(self, data):

        if isinstance(data, str):

            if os.path.exists(os.path.expanduser(data)):
                name = os.path.basename(data)
                size = os.path.getsize(data)
                f_type = None
                last_modified = int(os.path.getmtime(data))
            else:
                raise NotImplementedError()
        else:

            if (
                not isinstance(data, collections.abc.Mapping)
                and isinstance(data, collections.abc.Iterable)
                and len(data) == 1
            ):
                data = list(data)[0]

            if isinstance(data, collections.abc.Mapping):

                if len(data) == 1:
                    value = next(iter(data.values()))

                    if (
                        isinstance(value, collections.abc.Mapping)
                        and isinstance(
                            value.get("metadata", None), collections.abc.Mapping
                        )
                        and isinstance(value.get("content", None), bytes)
                    ):
                        # means uploaded file from FileUpload widget
                        # TODO: maybe check file name just to be sure
                        data = value

                if "metadata" in data.keys() and "content" in data.keys():
                    name = data["metadata"]["name"]
                    size = data["metadata"]["size"]
                    f_type = data["metadata"].get("type", None)
                    last_modified = data["metadata"]["lastModified"]
                else:
                    raise ValueError(f"Can't parse dict to file object: {data}")
            else:
                raise TypeError(
                    f"Can't create file object: invalid input type '{type(data)}'"
                )

        f = DharpaFile(name=name, size=size, type=f_type, last_modified=last_modified)
        return f

    name = Unicode()
    type = Unicode(allow_none=True)
    size = Integer()
    last_modified = Integer(allow_none=True)
    content = Bytes()

    def __repr__(self):

        if self.type:
            t = f" type={self.type}"
        else:
            t = ""

        return f"DharpaFile(name={self.name} size={self.size}{t})"


class DharpaFiles(object):
    @classmethod
    def create(self, data) -> "DharpaFiles":

        result = []

        if not data:
            return DharpaFiles()

        if isinstance(data, str):
            data = [data]

        if isinstance(data, collections.abc.Mapping):
            first_key = next(iter(data.keys()))
            if (
                isinstance(first_key, str)
                and isinstance(data[first_key], collections.abc.Mapping)
                and isinstance(
                    data[first_key].get("metadata", None), collections.abc.Mapping
                )
                and isinstance(data[first_key].get("content", None), bytes)
            ):

                for v in data.values():
                    f = DharpaFile.create(v)
                    result.append(f)
            else:
                f = DharpaFile.create(data)
                result.append(f)

        elif isinstance(data, collections.abc.Iterable):
            for d in data:
                f = DharpaFile.create(d)
                result.append(f)

        return DharpaFiles(*result)

    def __init__(self, *files: DharpaFile):

        self._files: typing.Iterable[DharpaFile] = files

    @property
    def files(self) -> typing.Iterable[DharpaFile]:
        return self._files

    def __repr__(self):

        return f"DharpaFiles(files={self.files})"


class FileSetValue(HasTraits):

    file_set = traitlets.Instance(klass=DharpaFiles, allow_none=True)


class FilesCollectionModule(DharpaModule):

    _module_name = "files_collection"

    def _create_inputs(self, **config) -> HasTraits:
        class FilesCollectionValueInput(HasTraits):
            files = traitlets.Any()

        return FilesCollectionValueInput()

    def _create_outputs(self, **config) -> HasTraits:

        return FileSetValue()

    def _process(self, files):

        d_files = DharpaFiles.create(files)
        return {"file_set": d_files}


class TextCorpus(object):
    def __init__(self, file_set: DharpaFiles):

        self._file_set: DharpaFiles = file_set

        self._corpus: typing.Mapping[str, str] = None  # type: ignore

    def file_set(self) -> DharpaFiles:
        return self._file_set

    def corpus(self) -> typing.Mapping[str, str]:

        if self._corpus is not None:
            return self._corpus

        self._corpus = {}
        for f in self._file_set.files:
            self._corpus[f.name] = f.content

        return self._corpus


class TextCorpusValue(HasTraits):

    text_corpus = Instance(klass=TextCorpus)


class CorpusFromFiles(DharpaModule):

    _module_name = "corpus_from_files"

    def _create_inputs(self, **config) -> HasTraits:

        return FileSetValue()

    def _create_outputs(self, **config) -> HasTraits:

        return TextCorpusValue()

    def _process(self, **inputs) -> typing.Mapping[str, typing.Any]:

        file_set: DharpaFiles = inputs["file_set"]
        result = TextCorpus(file_set=file_set)
        return {"text_corpus": result}
