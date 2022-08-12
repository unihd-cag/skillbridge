.. _tables_vectors.rst:

Tables and Vectors
==================

SKILL provides two data structures called ``table`` and ``vector``.
These are mapped similar to remote objects which means that the full content
of these data structures is never send to the python side unless requested.

The following examples assume that the skillbridge is running and a workspace
was opened like this:

.. code-block:: python

    from skillbridge import Workspace, Symbol
    ws = Workspace.open()

Tables
------

You can create a new table

.. code-block:: python

    t = ws.make_table('MyTable')
    # translates to makeTable("MyTable")

Or access an existing table (e.g. through a global variable)

.. code-block:: python

    t = ws.__.existing_table


Now ``t`` behaves like a python dictionary.


>>> t['x'] = 1
>>> t[2] = 3
>>> t[Symbol('x')] = 4
>>> t['x']
1
>>> t[2]
3
>>> t[Symbol('x')]
4
>>> t['missing']
Traceback (most recent call last):
    ...
KeyError: 'missing'
>>> t.get('missing')
None
>>> dict(t)
{'x': 1, 2: 3, Symbol('x'): 4}

It is possible to provide a default value like this:

.. code-block:: python

    t = ws.make_table('MyDefaultTable', None)
    # translates to makeTable("MyDefaultTable" nil)

>>> t['missing']
None

.. warning::

    The default value is evaluated on the SKILL side. That means only
    values that can be safely send to SKILL are possible. Empty containers
    and ``False`` are converted to ``None`` as usual.

    >>> ws.make_table('nil', [])['missing']  # translates to makeTable("nil" nil)
    None


As a convenience the attribute access to tables is an alias for item access with ``Symbol`` keys.

.. code-block:: python

    t = ws.make_table('Table')
    t.snake_case = 10
    print(t[Symbol('snakeCase')])  # prints 10
    t[Symbol('snakeCase')] = 20
    print(t.snake_case)  # prints 20

Vectors
-------

Vectors behave like python sequences with a somewhat fixed length. Note, that
vectors without a default value behave different from the usual python lists.

.. code-block:: python

    v = ws.make_vector(10)
    # translates to makeVector(10)

>>> len(v)
10
>>> v[0]
Traceback (most recent call last):
    ...
IndexError: 0
>>> list(v)
[]

You have to fill the "empty" slots of the vector before you can use them

>>> v[0] = 1
>>> v[2] = 3
>>> list(v)
[1]
>>> v[1] = 2
>>> list(v)
[1, 2, 3]

Vectors with a default value behave more like python sequences

.. code-block:: python

    v = ws.make_vector(5, 0)
    # translates to makeVector(5 0)

>>> list(v)
[0, 0, 0, 0, 0]
>>> v[0]
0
>>> v[0] = 10
>>> list(v)
[10, 0, 0, 0, 0]
