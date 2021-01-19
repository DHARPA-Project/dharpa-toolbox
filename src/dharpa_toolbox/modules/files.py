# -*- coding: utf-8 -*-

import collections
import os
import typing
from pathlib import Path

import traitlets
from traitlets import Bytes, HasTraits, Integer, Unicode

from .core import DharpaModule


class DharpaFile(HasTraits):
    @classmethod
    def create(self, data):

        if isinstance(data, Path):
            data = data.as_posix()

        if isinstance(data, str):

            if os.path.exists(os.path.expanduser(data)):
                data = os.path.expanduser(data)
                name = os.path.basename(data)
                size = os.path.getsize(data)
                f_type = None
                last_modified = int(os.path.getmtime(data))
                with open(data, "rb") as f:
                    content = f.read()
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

                content = data["content"]
            else:
                raise TypeError(
                    f"Can't create file object: invalid input type '{type(data)}'"
                )

        f = DharpaFile(
            name=name,
            size=size,
            type=f_type,
            last_modified=last_modified,
            content=content,
        )
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

        if isinstance(data, (str, Path)):
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


class ReadFilesModule(DharpaModule):
    """Reads the content of one or multiple files into a dictionary.

    The input can either be:
      - a string: the string must be the path to a file
      - a list of strings: each string must be the path to a file
      - a dict: each key is the id of a file (usually the file name), and the value is a dict with 'metadata' and 'content' keys (see FileUpload widget for details)

    The 'content_map' output value is a dict with the file id as key, and the content the decoded utf-8 text, as read from the file(s).

    """

    _module_name = "file_reader"

    def _create_inputs(self, **config) -> HasTraits:
        class FilesCollectionValueInput(HasTraits):
            files = traitlets.Any()

        return FilesCollectionValueInput()

    def _create_outputs(self, **config) -> HasTraits:
        class ReadFilesValueOutput(HasTraits):
            content_map = traitlets.Dict(key_trait=Unicode(), value_trait=Unicode())

        return ReadFilesValueOutput()

    def _process(self, files):

        d_files = DharpaFiles.create(files)
        text_map = {}
        for f in d_files.files:
            text_map[f.name] = f.content.decode("utf-8")

        return {"content_map": text_map}
