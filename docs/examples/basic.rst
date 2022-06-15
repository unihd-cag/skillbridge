.. _basic:

Basic Examples
==============

.. code-block:: python

    from skillbridge import Workspace
    
    ws = Workspace.open()
    cell_view = ws.ge.get_edit_cell_view()

    print(dir(cell_view))
    print(cell_view.b_box)
    
    cell_view = ws.db.open_cell_view("lib", "cell_name", "view_name")

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

**Passing Quoted Symbols**

Some Skill functions accept quoted symbols e.g. ``'someSymbol``. For this simple case you can use
the ``Symbol`` wrapper class in python.

>>> ws.ns.some_function(Symbol('someSymbol'))
...

*Skill equivalent:* ``nsSomeFunction('someSymbol)``

**Calling functions with keyword arguments**

Some Skill functions have named arguments (key arguments). This can be seen in the documentation.

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
are key parameters. These are translated to keyword arguments in python:

>>> ws.le.compute_area_density(window, llp_spec, depth=some_value, region=some_value)
[...]

*Skill equivalent:* ``leComputeAreaDensity(window llpSpec ?depth someValue ?region someValue)``

.. warning::

    On the python side you must use keyword arguments **if and only if** the Skill
    function has a named parameter.

Some functions even take lists of key arguments. For this case we provide the ``keys`` function in
python:

>>> from skillbridge import keys
>>> ws._.some_function([keys(x=1, y=1), keys(x=2, y=2])
[...]

*Skill equivalent:* ``someFunction( list( list(?x 1 ?y 1) list(?x 2 ?y 2) ) )``

Should the need arise it is also possible to directly create these key symbols for Skill with the
``Key`` class.

>>> from skillbridge import Key
>>> Key('xyz')
Key(xyz)

*Skill equivalent:* ``?xyz``


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

**Accessing global variables**

Sometimes you need access to certain global variables (e.g. ``stdout``). All global variables
are grouped under the prefix ``__`` (two underscores).

>>> ws.__.stdout
<remote open_file '*stdout*'>
