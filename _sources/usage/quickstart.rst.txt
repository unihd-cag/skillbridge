.. _quickstart:

Quickstart
==========

Starting the Server
-------------------

Open the Skill console in Virtuoso and type

.. code-block:: lisp

    load("<PATH-TO-SKILL-IPC-SCRIPT>")

You can obtain the correct path from the python library like this:

.. code-block:: sh

    python -m skillbridge


Read more about :ref:`server`.

Connecting to the Server
------------------------


.. code-block:: python

    from skillbridge import Workspace

    ws = Workspace.default()


Usage examples
--------------


**Accessing the currently open edit cell view**

.. code-block:: python

    cell_view = ws.ge.get_edit_cell_view()


*Skill equivalent:* ``cellView = geGetEditCellView()``

**Inspecting available properties**

>>> dir(cell_view)
['DBUPerUU', 'any_inst_count', 'area_boundaries', 'assoc_text_displays', 'b_box', ...]

*Skill equivalent:* ``cellView->?``

or type ``cell_view.<TAB>`` in ipython/jupyter

**Reading properties**


>>> print(cell_view.b_box)
[[0, 10], [0, 10]]


*Skill equivalent:* ``cellView->bBox``

.. hint::

    All Skill identifiers like ``bBox`` or ``cellViewType`` are
    transformed to snake case on the python side ``b_box`` and ``cell_view_type``.
    You may choose whether you want to use the original camel-case names or the
    transformed snake-case variants.

    >>> cell_view.bBox
    [[0, 10], [0, 10]]
    >>> cell_view.b_box
    [[0, 10], [0, 10]]


**Calling global functions**

The Skill functions are separated based on their prefix (compare
``dbOpenCellView`` vs ``schCreateWire``). Functions with the same
prefix are grouped together inside a python :class:`client.functions.FunctionCollection`.

>>> ws.db.open_cell_view("lib", "cell_name", "view_name")  # dbOpenCellView
<remote object ...>

*Skill equivalent:* ``dbOpenCellView("lib", "cell_name", "view_name")``

>>> ws.sch.create_wire(...)  # schCreateWire
[<remote object ...>]

*Skill equivalent:* ``schCreateWire(...)``

**Calling functions with keyword arguments**

Some Skill functions have named arguments. This can be seen in the documentation.

>>> ws.le.compute_area_density
<remote function>
leComputeAreaDensity(
w_windowId
l_lppSpec
[ ?depth x_depth ]
[ ?region l_region ]
)

*Skill equivalent:* ``help(leComputeAreaDensity)``

We can see that the function takes four arguments: ``w_windowId`` and ``l_lppSpec``
are positional arguments and can be passed as shown above. But ``depth`` and ``region``
are named parameters. These are translated to keyword arguments in python:

>>> ws.le.compute_area_density(window, llp_spec, depth=some_value, region=some_value)
[...]

*Skill equivalent:* ``leComputeAreaDensity(window llpSpec ?depth someValue ?region someValue)``

.. warning::

    On the python side you must use keyword arguments **if and only if** the Skill
    function has a named parameter.

**Calling methods**

Some Skill functions receive a remote object as their first argument.

>>> ws.db.full_path
<remote method 'dbFullPath'>
dbFullPath(
d_cellView
)


These functions can be treated like methods by calling them directly from the
corresponding remote object:

>>> cell_view.db_full_path()  # not the '_' instead of '.'
# same output as ws.db.full_path(cell_view)

*Skill equivalent:* ``dbFullPath(cellView)``

.. note::

    In order to prevent name collisions, the method name contains the prefix of the
    Skill function while the global functions do not, since they are already grouped
    under that prefix.