# Python-Skill Bridge

[![PyPI version](https://badge.fury.io/py/skillbridge.svg)](https://badge.fury.io/py/skillbridge)
![build](https://github.com/unihd-cag/simple-geometry/workflows/Python%20package/badge.svg)

### Prerequisites

- Python 3.6 or higher
- pip
- IC 6.1.7 or ICADV/M or higher

### Features

- Run Virtuoso's Skill functions from Python
- Automatically translate all Skill objects to Python
- Automatically translate Python numbers, booleans, strings, lists and dictionaries to Skill
- Retrieve Skill function documentation in Python
- Convenient tab-completion (+ jupyter support)
  - object attributes
  - global function list
  - methods

Read more in the [full documentation](https://unihd-cag.github.io/skillbridge/).

### Installation

```bash
pip install skillbridge
```

Add the `--user`  option if you don't want to install it systemwide.

Before you can use the Skill bridge you must generate the function definitions from
Virtuoso via the Skill console.

1. Type `skillbridge path` into your shell to acquire the correct `PATH-TO-IPC-SERVER`
2. Open Virtuoso
2. Type these commands into the Skill console
    - `load("PATH-TO-IPC-SERVER")`

After that you can also generate the static completion stub files. This is useful for code completion
in certain IDEs (e.g. PyCharm)

- Type `skillbridge generate` into your shell.

### Updating

In order to update the python package type this

```bash
pip install skillbridge --upgrade
```

### Examples

**_Note:_** All these examples assume that the Skill server is running. You can
start it by typing the following command into the Skill console.

```lisp
load("PATH-TO-IPC-SERVER")
pyStartServer
```

##### Connecting to the server

```python
from skillbridge import Workspace

ws = Workspace.open()
```

##### Accessing the currently open edit cell view

```python
cell_view = ws.ge.get_edit_cell_view()
```

##### Inspecting available properties

```python
>>> dir(cell_view)
['DBUPerUU', 'any_inst_count', 'area_boundaries', 'assoc_text_displays', 'b_box', ...]
```

or type `cell_view.<TAB>` in jupyter/ipython

##### Reading properties

```python
>>> print(cell_view.b_box)
[[0, 10], [2, 8]]
```
