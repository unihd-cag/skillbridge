# Python-Skill Bridge

### Features

- Run Virtuoso's Skill functions from Python
- Automatically translate all Skill objects to Python
- Automatically translate Python numbers, booleans, strings, lists and dictionaries to Skill
- Retrieve Skill function documentation in Python
- Convenient tab-completion (+ jupyter support)
  - object attributes
  - global function list
  - methods

Read more in the [full documentation](#).

### Installation

```bash
pip install skillbridge
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

##### Multiple Virtuoso Instances

You can run multiple Virtuoso instances and have a running server inside
each of them. However, in order to match the clients and server correctly
you must start and connect a bit differently:

**Virtuoso Instance 1**

```lisp
; This starts the server with the default id
load("PATH-TO-IPC-SERVER")
pyStartServer
```

**Python Client 1**

```python
ws = Workspace.open()
```

**Virtuoso Instance 2**

```lisp
; This starts the server with a custom id
load("PATH-TO-IPC-SERVER")
pyStartServer "some-id"
```

**Python Client 2**

```python
ws = Workspace.open('some-id')
```

You could even open both Workspaces in a single python session, but it
is not possible to run two python servers in a single Virtuoso session.