.. _globals:

Global Variables
================

Sometimes it is inefficient and unnecessary to pass large lists between python and SKILL.
In this case global variables come in handy:

.. code-block:: python

    from skillbridge import Workspace

    ws = Workspace.open()

    my_globals = ws.globals('my_globals')
    # assign a value from python
    my_globals.x << 2
    my_globals.y << 3

    # read variable on python side
    print(my_globals.x() + my_globals.y())

    # use variable on SKILL side
    print(ws['plus'](my_globals.x, my_globals.y))


You can assign values from a skillbridge function

.. code-block:: python

    from skillbridge import Workspace

    ws = Workspace.open()

    my_globals = ws.globals('my_globals')
    # important: use `var` here
    my_globals.shapes << ws.ge.get_sel_set.var()

    # length is calculated on SKILL side
    print(ws['length'](my_globals.shapes))


The higher-order functions `foreach`, `mapcar` and `setof` are also mapped:

.. code-block:: python

    from skillbridge import Workspace, loop_var

    ws = Workspace.open()

    my_globals = ws.globals('my_globals')
    my_globals.shapes << ws.ge.get_sel_set.var()

    # get the boxes
    my_globals.boxes << my_globals.shapes.map(loop_var.b_box)

    # filter rectangles
    my_globals.rects << my_globals.shapes.filter(loop_var.obj_type == 'rect')

    # delete all shapes
    my_globals.shapes.for_each(ws.db.delete_object.var(loop_var))

`mapcar`  also supports multiple listst

.. code-block:: python

    from skillbridge import Workspace, loop_var_i, loop_var_j

    ws = Workspace.open()

    my_globals = ws.globals('my_globals')
    my_globals.x << [1, 2, 3]
    my_globals.y << [1, 2, 4]
    my_globals.z << my_globals.x.map(loop_var_i + loop_var_j, j=my_globals.y)
    print(my_globals.z())  # [2, 4, 7]
