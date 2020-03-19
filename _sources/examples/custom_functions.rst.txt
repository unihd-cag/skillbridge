Manually Registering Functions
==============================


The ``skillbridge`` will only export functions that are documented in
the running Virtuoso instance. If you need functions that are not documented there
but still exist, you can register them manually.
There are two methods for this either with the prefix method which is a clean way to
categorize and define the function. Since some skill function definitions do not follow
the default camel case naming conventions or have not prefix, we also provide a way
to specify the function name.

Prefix register method
-----------------------

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

Direct method
--------------

In this example the skill method load is directly called.

.. code-block::
    python

    from skillbrige import Workspace
    ws = Workspace()
    ws['load']('exmapleFile.il')

Let us say you have a SKILL function called ``myFunction_def``.
You can call it in python like this. Pay attention this function must be
defined exist in your Virtuoso instance.

.. code-block::
    python

    from skillbrige import Workspace
    ws = Workspace()
    ws['myFunction_def'](...)

.. note::

   Keep in mind that the functions you get this way behave exactly like the functions from the
   prefix method, including keyword arguments.