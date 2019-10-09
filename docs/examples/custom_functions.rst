Manually Registering Functions
==============================

The ``skillbridge`` will only export functions that are documented in
the running Vivado instance. If you need functions that are not documented there
but still exist, you can register them manually.

Let's take a look at the following example.

.. code-block::
    python

    @ws.register
    def dbCheck(d_cellview) -> None:
        """
        A docstring
        """

This will register the function ``dbCheck`` which takes a single argument ``d_cellview``
and returns ``nil``. You may also write the function name in snake case: ``db_check``.

.. note::

    You must provide a return type annotation. Use ``None`` if you don't know the type
    or are unsure. You also must provide a doc string which describes what the function
    actually does.

There are three ways to specify arguments.

1. Positional, required arguments by naming the python parameter accordingly
2. Positional, optional arguments by adding the type annotation ``Optional``
3. Keyword arguments by assigning a name to the variable

The next example shows all three uses

.. code-block::
    python

    from typing import Optional

    @ws.register
    def myFunction(required, optional: Optional, keyword="someName") -> "someReturnValue":
        """
        A nice doc string, that explains the function
        """

You can use the function like this:

>>> ws.my.function
<remote function 'myFunction'>
myFunction(
    required
    [ optional ]
    [ ?someName keyword ]
=> someReturnValue
A nice doc string, that explains the function

.. warning::

    Obviously this only **registers** the function, but it does not define it
    in Skill. If you actually call ``myFunction`` you will get the error:

    ``undefined function myFunction``