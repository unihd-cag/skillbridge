# Python-Skill Bridge ![build](https://travis-ci.org/unihd-cag/skillbridge.svg?branch=master) ![codecov](https://codecov.io/gh/unihd-cag/skillbridge/branch/master/graph/badge.svg)

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
pip install git+https://github.com/unihd-cag/skillbridge.git
```

Before you can use the Skill bridge you must generate the function definitions from
Virtuoso via the Skill console.

1. Type `python -m skillbridge` into your shell to acquire the correct `PATH-TO-IPC-SERVER`
2. Open Virtuoso
2. Type these commands into the Skill console
    - `load("PATH-TO-IPC-SERVER")`
    - `pyDumpFunctionDefinitions "<install>"` (`"<install>"` is not a placeholder, type it as is)

**_Note:_** Generating the function definitions is very slow and will take several
minutes. Don't cancel the command.

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
