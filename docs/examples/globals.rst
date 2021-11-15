.. _basic:

Global Variables
================

Sometimes it is inefficient and unnecessary to pass large lists between python and SKILL.
In this case global variables come in handy:

.. code-block:: python
    from skillbridge import Workspace

    ws = Workspace.open()

    with ws.globals('my_globals') as my_globals:
        # assign a value from python
        my_globals.x = 2
        my_globals.y = 3

        # read variable on python side
        print(my_globals.x() + my_globals.y())

        # use variable on SKILL side
        print(ws['add'](my_globals.x, my_globals.y))

       # variables are set to nil here



If you don't want the variables to be reset, don't use a context manager

.. code-block:: python
    from skillbridge import Workspace

    ws = Workspace.open()

    my_globals = ws.globals('my_globals')
    my_globals.x = 2

    # variable is never set to nil

You can assign values from a skillbridge function

.. code-block:: python
    from skillbridge import Workspace

    ws = Workspace.open()

    my_globals = ws.globals('my_globals')
    # important: use `raw` and `lazy`
    my_globals.shapes.raw = ws.ge.get_sel_set.lazy()


The higher-order functions `foreach`, `mapcar` and `setof` are also mapped:

.. code-block:: python
    from skillbridge import Workspace, Var, loop_var

    ws = Workspace.open()

    my_globals = ws.globals('my_globals')
    my_globals.shapes.raw = ws.ge.get_sel_set.lazy()

    # get the boxes
    my_globals.boxes.raw = my_globals.shapes.map(loop_var.b_box)

    # filter rectangles
    my_globals.rects.raw = my_globals.shapes.filter(loop_var.obj_type == 'rect')

    # delete all shapes
    my_globals.shapes.foreach(ws.db.delete_object.lazy(loop_var))
