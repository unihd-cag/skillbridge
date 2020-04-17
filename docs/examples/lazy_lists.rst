.. _lazy_lists:

Handling Large Lists
====================

Sometimes for-loops on the Python side are too slow, because every iteration sends a SKILL command and waits for the
answer to it. In some cases we can "move" the for-loop to the SKILL side.


This naive code example queries all shapes and deletes some of them. The attribute access and the delete function both
trigger a SKILL command on each iteration.


.. code-block::
    python

    cv = ws.ge.get_edit_cell_view()

    for shape in cv.shapes:
        if shape.layer == 'M1':
            ws.db.delete_object(shape)


Another problem occurs when only a single item of a long list is needed. The following code example receives the
complete list from SKILL twice and then takes a single element/and the length out of it.

.. code-block::
    python

    cv = ws.ge.get_edit_cell_view()

    print(cv.shapes[0])
    print(len(cv.shapes))


The class ``LazyList`` can help us in these situations. The first step is to use the ``lazy`` attribute of the remote
object. After that filtering, for-loops and accessing single items becomes very efficient.

.. code-block::
    python

    cv = ws.ge.get_edit_cell_view()
    shapes = cv.lazy.shapes  # notice the `lazy` attribute

    print(shapes[0])  # only one item is transferred
    print(len(shapes))  # length is calculated in SKILL

    shapes.filter(layer='M1').foreach(ws.db.delete_object)  # filtering and deletion is done in SKILL

    print(shapes[:])  # in case you still need it: the whole list


.. warning::

    Try to combine multiple filters into a single call to ``LazyList.filter``. Multiple filter calls in Python will
    result in multiple filter calls in SKILL.

    .. code-block:: python

        shapes.filter(layer='M1', purpose='...')  # better
        shapes.filter(layer='M1').filter(purpose='...')  # worse


.. warning::

    Don't use C-like for loops with ``LazyList``

    .. code-block:: python

        for i in range(len(shapes)):
            print(shapes[i])  # very slow

    This runs in quadratic time.


Advanced usage of ``LazyList.foreach``
--------------------------------------

``LazyList.foreach`` has three forms. You can pass a remote function with arguments, without arguments or a lazily
evaluated remote function.

The simple form is without arguments. In this case every item of the list is passed as the single argument to the
function.

.. code-block:: python

    shapes.foreach(ws.db.delete_object)

If you need additional arguments, you can use the following form. In this example the function is called with two
arguments. The first is the element of the list and the second is a constant we provided.

.. code-block:: python

    shapes.foreach(ws.example.move_object, LazyList.arg, [10, 10])

Alternatively you can use the following syntax which is equivalent to the second form.

.. code-block:: python

    shapes.foreach(ws.example.move_object.lazy(LazyList.arg, [10, 10]))  # notice the `lazy` attribute
