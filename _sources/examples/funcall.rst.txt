.. _funcall:

Directly call function objects
==============================

Some Virtuoso functions return ``funobj`` objects. There is a shortcut on the python side to call
these objects like ordinary functions.

.. code-block:: python 

    from skillbridge import Workspace

    
    ws = Workspace.open()

    fun = ...  # obtain a funobj
    fun
    # <remote funobj@...>

    fun()
    # SKILL equivalent: funcall(fun)

    fun(1, 2, 3)
    # SKILL equivalent: funcall(fun 1 2 3)

    fun(x=1, y=2, z=3)
    # SKILL equivalent: funcall(fun ?x 1 ?y 2 ?z 3)
