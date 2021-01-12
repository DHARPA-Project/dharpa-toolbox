# Installation

There are three ways to install *dharpa-toolbox* on your machine. Via a manual binary download, an install script, or installation of the python package.

## Binaries

To install `dharpa-toolbox`, download the appropriate binary from one of the links below, and set the downloaded file to be executable (``chmod +x dharpa-toolbox``):

  - [Linux](https://s3-eu-west-1.amazonaws.com/dev.dl.frkl.io/linux-gnu/dharpa-toolbox)
  - [Windows](https://s3-eu-west-1.amazonaws.com/dev.dl.frkl.io/windows/dharpa-toolbox.exe)
  - [Mac OS X](https://s3-eu-west-1.amazonaws.com/dev.dl.frkl.io/darwin/dharpa-toolbox)


## Install script

Alternatively, use the 'curly' install script for `dharpa-toolbox`:

``` console
curl https://gitlab.com/frkl/dharpa-toolbox/-/raw/develop/scripts/install/dharpa-toolbox.sh | bash
```


This will add a section to your shell init file to add the install location (``$HOME/.local/share/frkl/bin``) to your ``$PATH``.

You might need to source that file (or log out and re-log in to your session) in order to be able to use *dharpa-toolbox*:

``` console
source ~/.profile
```


## Python package

The python package is currently not available on [pypi](https://pypi.org), so you need to specify the ``--extra-url`` parameter for your pip command. If you chooose this install method, I assume you know how to install Python packages manually, which is why I only show you an example way of getting *dharpa-toolbox* onto your machine:

``` console
> python3 -m venv ~/.venvs/dharpa-toolbox
> source ~/.venvs/dharpa-toolbox/bin/activate
> pip install --extra-index-url https://pkgs.frkl.io/frkl/dev --extra-index-url https://pkgs.frkl.dev/pypi dharpa-toolbox
Looking in indexes: https://pypi.org/simple, https://pkgs.frkl.io/frkl/dev
Collecting dharpa-toolbox
  Downloading http://pkgs.frkl.io/frkl/dev/%2Bf/ee3/f57bd91a076f9/dharpa-toolbox-0.1.dev24%2Bgd3c4447-py2.py3-none-any.whl (28 kB)
...
...
...
Successfully installed aiokafka-0.6.0 aiopg-1.0.0 ... ... ...
> dharpa-toolbox --help
Usage: dharpa-toolbox [OPTIONS] COMMAND [ARGS]...
   ...
   ...
```
