[![PyPI status](https://img.shields.io/pypi/status/dharpa-toolbox.svg)](https://pypi.python.org/pypi/dharpa-toolbox/)
[![PyPI version](https://img.shields.io/pypi/v/dharpa-toolbox.svg)](https://pypi.python.org/pypi/dharpa-toolbox/)
[![PyPI pyversions](https://img.shields.io/pypi/pyversions/dharpa-toolbox.svg)](https://pypi.python.org/pypi/dharpa-toolbox/)
[![Code style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

# dharpa-toolbox

*Tools and utilities for the DHARPA project*


## Description

This is prototype-level code that will not make it (for the most part) into production, it's for proof-of-concept
and tech-validation purposes only. Don't rely on any of the models, schemas, whatever else in here.
There are some things that are not implemented, and probably won't ever be (default values in a schema for examples are just ignored for now).

The code in here lets developers create workflows by assembling pre-created modules (that are bascially Python classes) using
a json or yaml file. For examples of such workflow files, check the ``src/resources/workflows`` folder.

I've prepared 3 workflows that mirror logic gates: ``nand``, ``nor``, ``xor``. All developers should be familiar with those,
and the fact that complex logic gates can be assembled out of a combination of ``and``, ``or`` and ``not`` gates. Those basic modules are
written in Python, and can be found under ``src/dharpa/processing/core/logic_gates``.
I figured that using logic gates makes sense, it's easy to recognise the graphs created out of such workflows, since
that is fairly similar to how complex gate-structures are visualized anyway. Also, in this scenario we don't have to
worry yet about data transfer, since all we are dealing with are booleans. And lastly, this will be very helpful for testing
the code that manages workflow/pipeline logic, since we can predict very easily the correct output for even complex
workflow structures.

The other approach I've prepared for is using a ``dummy`` module. This is a Python class (in ``src/dharpa/processing/core/dummy``)
whose input- and output-schema as well as the output values can be hard-coded, so it's well suited to
create the structure of a workflow without having to implement any of the business logic (we just assume that the pre-set
output values will be the right result for whatever input there is). Using only 'dummy' modules is a good first step after the wireframe for a workflow is ready,
because it forces the workflow creator to think about the inputs and outputs, their schema, and how everything is connected.

Check out the 'Usage' section for examples.

# Development

## Requirements

- Python (version >=3.6) (only tested with Python 3.9 so far though)
- pip, virtualenv
- git
- make
- [direnv](https://direnv.net/) (optional)


## Prepare development environment

Notes:

- if not using *direnv*, you have to setup and activate your Python virtualenv yourself, manually, before running ``make init``, something like:

```console
git clone https://github.com/DHARPA-Project/dharpa-toolbox
cd dharpa-toolbox
python3 -m venv .venv
source .venv/bin/activate
make init
```

## ``make`` targets

- ``init``: init development project (install project & dev dependencies into virtualenv, as well as pre-commit git hook)
- ``mypy``: run mypy tests
- ``test``: run unit tests
- ``clean``: clean build directories

For details (and other, minor targets), check the ``Makefile``.

## Usage examples

### Commandline interface

The commandline interface currently has one sub-command: ``module``. This lets the user manage and execute the currently implemented
modules and workflows.

#### list modules

To get a list of all of those, use the ``list`` sub-command (use the ``--details`` flag for more verbose information):

```shell
➜ dharpa-toolbox module list

- module: and
  doc: Returns 'True' if both inputs are 'True'.
  is_pipeline: False
- module: dummy
  doc: Module that simulates processing, but uses hard-coded outputs as a result.
  is_pipeline: False
- module: nand
  doc: Returns 'True' if both inputs are 'False'.
  is_pipeline: True
- module: nor
  doc: -- n/a --
  is_pipeline: True
- module: not
  doc: Negates the input.
  is_pipeline: False
- module: or
  doc: Returns 'True' if one of the inputs is 'True'.
  is_pipeline: False
- module: single_module
  doc: xxx
  is_pipeline: True
- module: topic_modelling
  doc: topic modelling workflow
  is_pipeline: True
- module: xor
  doc: Returns 'True' if exactly one of it's two inputs is 'True'.
  is_pipeline: True
```

#### module info

To display information about one or several specific modules or workflows, use ``info`` (this is currently not really useful):

```shell
➜ dharpa-toolbox module info xor

- module: xor
  doc: Returns 'True' if exactly one of it's two inputs is 'True'.
  is_pipeline: True
  configuration options:
    input_aliases:
      type: object
      required: no (default: {})
    modules:
      type: array
      required: yes
    output_aliases:
      type: object
      required: no (default: {})
```

#### run module

To execute a workflow, we use the ``run`` command:

```shell
➜ dharpa-toolbox module run xor

Not all inputs ready.
  a: None
  b: None
```

As you can see here, this doesn't work yet because we need to give the module its inputs. Currently, only inputs via
file-path is supported. A few example inputs are under the ``examples`` sub-directory. Let's try that:

``` shell
➜ dharpa-toolbox module run xor examples/inputs_logic_all_true.json

processing started: xor.xor
processing started: xor.or
...
...
...
processing finished: xor.and
processing finished: xor.xor

Result:

{'y': False}
```

#### display the current state of a module

This is relevant for every user-facing interface that wants to enable interactive module execution. Because those systems
need to know the current state of a workflow and potentially it's internal structure.

##### via json

In most cases we will want a data structure that describes that state.

Here is an example for a 'stale' module (that doesn't have any inputs yet):

```shell
➜ dharpa-toolbox module state-json nand

processing started: nand.nand
processing finished: nand.nand

{
  "alias": "nand",
  "address": "nand.nand",
  "type": "nand",
  "is_pipeline": true,
  "state": "stale",
  "inputs": {
    "a": {
      "schema": {
        "type": "boolean",
        "default": null
      },
      "value": null
    },
    "b": {
      "schema": {
        "type": "boolean",
        "default": null
      },
      "value": null
    }
  },
  "outputs": {
    "y": {
      "schema": {
        "type": "boolean",
        "default": null
      },
      "value": null
    }
  },
  "execution_stage": null,
  "doc": "Returns 'True' if both inputs are 'False'.",
  "pipeline_structure": null
}
```

And this is how a module state looks like with inputs:

```shell
➜ dharpa-toolbox module state-json nand examples/inputs_logic_all_false.json

processing started: nand.nand
processing started: nand.and
processing finished: nand.and
processing started: nand.not
processing finished: nand.not
processing finished: nand.nand

{
  "alias": "nand",
  "address": "nand.nand",
  "type": "nand",
  "is_pipeline": true,
  "state": "results_ready",
  "inputs": {
    "a": {
      "schema": {
        "type": "boolean",
        "default": null
      },
      "value": false
    },
    "b": {
      "schema": {
        "type": "boolean",
        "default": null
      },
      "value": false
    }
  },
  "outputs": {
    "y": {
      "schema": {
        "type": "boolean",
        "default": null
      },
      "value": true
    }
  },
  "execution_stage": null,
  "doc": "Returns 'True' if both inputs are 'False'.",
  "pipeline_structure": null
}
```

Since ``nand`` is a workflow that internally uses an ``and`` and ``not`` module, we can also investigate that internal structure (using the ``--show-structure`` flag:

```shell
➜ dharpa-toolbox module state-json nand --show-structure examples/inputs_logic_all_false.json

processing started: nand.nand
processing started: nand.and
processing finished: nand.and
processing started: nand.not
processing finished: nand.not
processing finished: nand.nand

{
  "alias": "nand",
  "address": "nand.nand",
  "type": "nand",
  "is_pipeline": true,
  "state": "results_ready",
  "inputs": {
    "a": {
      "schema": {
        "type": "boolean",
        "default": null
      },
      "value": false
    },
    "b": {
      "schema": {
        "type": "boolean",
        "default": null
      },
      "value": false
    }
  },
  "outputs": {
    "y": {
      "schema": {
        "type": "boolean",
        "default": null
      },
      "value": true
    }
  },
  "execution_stage": null,
  "doc": "Returns 'True' if both inputs are 'False'.",
  "pipeline_structure": {
    "workflow_id": "nand",
    "modules": [
      {
        "module": {
          "alias": "and",
          "address": "nand.and",
          "type": "and",
          "is_pipeline": false,
          "state": "results_ready",
          "inputs": {
            "a": {
              "schema": {
                "type": "boolean",
                "default": null
              },
              "value": false
            },
            "b": {
              "schema": {
                "type": "boolean",
                "default": null
              },
              "value": false
            }
          },
          "outputs": {
            "y": {
              "schema": {
                "type": "boolean",
                "default": null
              },
              "value": false
            }
          },
          "execution_stage": 1,
          "doc": "Returns 'True' if both inputs are 'True'.",
          "pipeline_structure": null
        },
        "input_connections": {
          "a": "__parent__.a",
          "b": "__parent__.b"
        },
        "output_connections": {
          "y": [
            "not.a"
          ]
        }
      },
      {
        "module": {
          "alias": "not",
          "address": "nand.not",
          "type": "not",
          "is_pipeline": false,
          "state": "results_ready",
          "inputs": {
            "a": {
              "schema": {
                "type": "boolean",
                "default": null
              },
              "value": false
            }
          },
          "outputs": {
            "y": {
              "schema": {
                "type": "boolean",
                "default": null
              },
              "value": true
            }
          },
          "execution_stage": 2,
          "doc": "Negates the input.",
          "pipeline_structure": null
        },
        "input_connections": {
          "a": "and.y"
        },
        "output_connections": {
          "y": [
            "__parent__.y"
          ]
        }
      }
    ],
    "workflow_input_connections": {
      "a": [
        "and.a"
      ],
      "b": [
        "and.b"
      ]
    },
    "workflow_output_connections": {
      "y": "not.y"
    }
  }
}
```

##### via a network graph

If we want a more visual overview of the workflow, we can also print out the network graph on the terminal (ideally, we'd have a
way better visualisation via the browser, but I guess this is good enough for now):

```shell
➜ dharpa-toolbox module state-graph nand examples/inputs_logic_all_false.json

processing started: nand.nand
processing started: nand.and
processing finished: nand.and
processing started: nand.not
processing finished: nand.not
processing finished: nand.nand

 ┌─────────────┐ ┌─────────────┐
 │user input: a│ │user input: b│
 │value: False │ │value: False │
 └──────────┬──┘ └─┬───────────┘
            │      │  
            v      v  
     ┌────────────────────┐  
     │    module: nand    │  
     │state: results_ready│  
     └──────────┬─────────┘  
                │  
                v  
      ┌──────────────────┐  
      │workflow output: y│  
      │   value: True    │  
      └──────────────────┘  
```

As before, we can choose to also look at the internal structure:

```shell
➜ dharpa-toolbox module state-graph nand --show-structure examples/inputs_logic_all_false.json

processing started: nand.nand
processing started: nand.and
processing finished: nand.and
processing started: nand.not
processing finished: nand.not
processing finished: nand.nand

   ┌─────────────┐   ┌─────────────┐  
   │user input: b│   │user input: a│  
   │value: False │   │value: False │  
   └──────┬──────┘   └────────┬────┘  
          │                   │  
          v                   v  
 ┌─────────────────┐ ┌─────────────────┐
 │input: nand.and.b│ │input: nand.and.a│
 │  type: boolean  │ │  type: boolean  │
 │  value: False   │ │  value: False   │
 └──────────────┬──┘ └─┬───────────────┘
                │      │  
                v      v  
         ┌────────────────────┐  
         │  module: nand.and  │  
         │state: results_ready│  
         └──────────┬─────────┘  
                    │  
                    v  
          ┌──────────────────┐  
          │output: nand.and.y│  
          │  type: boolean   │  
          │   value: False   │  
          └────────┬─────────┘  
                   │  
                   v  
          ┌─────────────────┐  
          │input: nand.not.a│  
          │  type: boolean  │  
          │  value: False   │  
          └─────────┬───────┘  
                    │  
                    v  
         ┌────────────────────┐  
         │  module: nand.not  │  
         │state: results_ready│  
         └──────────┬─────────┘  
                    │  
                    v  
          ┌──────────────────┐  
          │output: nand.not.y│  
          │  type: boolean   │  
          │   value: True    │  
          └─────────┬────────┘  
                    │  
                    v  
          ┌──────────────────┐  
          │workflow output: y│  
          │   value: True    │  
          └──────────────────┘  
```

Try that without inputs (or the partial input file ``examples/inputs_logic_one_input_missing.json`` to see how that changes
the state of the internal structure.

### Python library

Check out the two example notebooks:

 - [xor](https://github.com/DHARPA-Project/dharpa-toolbox/blob/develop/dev/xor.ipynb)
- [topic-modelling-dummy](https://github.com/DHARPA-Project/dharpa-toolbox/blob/develop/dev/topic_modelling_dummy.ipynb)
