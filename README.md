[![PyPI status](https://img.shields.io/pypi/status/dharpa-toolbox.svg)](https://pypi.python.org/pypi/dharpa-toolbox/)
[![PyPI version](https://img.shields.io/pypi/v/dharpa-toolbox.svg)](https://pypi.python.org/pypi/dharpa-toolbox/)
[![PyPI pyversions](https://img.shields.io/pypi/pyversions/dharpa-toolbox.svg)](https://pypi.python.org/pypi/dharpa-toolbox/)
[![Code style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

# dharpa-toolbox

*Tools and utilities for the DHARPA project*


## Description

Documentation still to be done.


# Development

## Requirements

- Python (version >=3.6)
- pip, virtualenv
- git
- make
- [direnv](https://direnv.net/) (optional)


## Prepare development environment

Notes:

- if using *direnv*, adjust the Python version in ``.envrc`` (should not be necessary)

``` console
git clone https://gitlab.com/frkl/dharpa-toolbox
cd dharpa-toolbox
mv .envrc.disabled .envrc
direnv allow   # if using direnv, otherwise activate virtualenv
make init
```

- if not using *direnv*, you have to setup and activate your Python virtualenv yourself, manually, before running ``make init``, something like:

```console
git clone https://gitlab.com/frkl/dharpa-toolbox
cd dharpa-toolbox
python3 -m venv .venv
source .venv/bin/activate
make init
```


## ``make`` targets

- ``init``: init development project (install project & dev dependencies into virtualenv, as well as pre-commit git hook)
- ``binary``: create binary for project (will install *pyenv* -- check ``scripts/build-binary`` for details)
- ``flake``: run *flake8* tests
- ``mypy``: run mypy tests
- ``test``: run unit tests
- ``docs``: create static documentation pages
- ``serve-docs``: serve documentation pages (incl. auto-reload)
- ``clean``: clean build directories

For details (and other, minor targets), check the ``Makefile``.


## Running tests

``` console
> make test
# or
> make coverage
```
