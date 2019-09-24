Remote Objects
==============

.. py:currentmodule:: skillbridge.client.objects

.. class:: RemoteObject

    :class:`RemoteObject` instances represent any object in Skill that is neither of the
    following types:

    - :class:`int`
    - :class:`float`
    - :class:`str`
    - :class:`bool`
    - :class:`list`
    - :class:`nil`

    .. method:: __getattr__

        Skill properties can be accessed like normal python attributes, provided the property
        exists on the Skill object

        >>> cell = ws.ge.get_edit_cell_view()
        [[0, 10], [0, 10]]

        Properties of Skill objects can again be :class:`RemoteObject` instances:

        >>> cell.cell_view
        <remote object db:0xHHHHHH @....>


    .. method:: __setattr__

        It is also possible to change the Skill properties using normal python attribute
        access. If the property does not exist on the skill side, it will be created.

        >>> cell.x = 123
        >>> cell.x
        123

        .. note::

            Changes to list are not synchronized with the Skill side at the moment

            >>> cell.data = [1, 2, 3]
            >>> cell.data.append(4)
            >>> cell.data
            [1, 2, 3]

            To work around this, you must manually assign the list back to the object

            >>> data = cell.data
            >>> data.append(4)
            >>> cell.data = data
            >>> cell.data
            [1, 2, 3, 4]

        .. warning::

            Creating new boolean properties on the Skill side show a strange behaviour

            >>> cell.new_bool_property = True
            >>> cell.new_bool_property
            "TRUE"  # instead of t

            >>> cell.new_bool_property = False
            >>> cell.new_bool_property
            "FALSE"  # instead of nil


    .. method:: __dir__

        All available Skill properties can be listed using this method. It looks up the
        properties inside skill using the expression ``__var -> ?`` and returns the
        property names as a list

        >>> dir(cell)
        ['DBUPerUU', 'any_inst_count', 'area_boundaries', 'assoc_text_displays', ...]

        Inside Jupyter/IPython this method is used to provide tab completion

        >>> cell.<TAB>
        # Shows a dropdown menu containing ['DBUPerUU', 'any_inst_count', ...]

        >>> cell?
        # Shows a window containing ['DBUPerUU', 'any_inst_count', ...]


    .. method:: __eq__

        Compares two :class:`RemoteObject` and returns whether they are considered equal.
        They are considered equal if the Skill identifiers are equal.

        .. code-block:: python

            cell = ws.ge.get_edit_cell_view()  # dbobject:0xHHHHHHH
            another = ws.ge.get_edit_cell_view()  # dbobject:0xHHHHHH

            assert cell == another


    .. method:: __ne__

        Compares two :class:`RemoteObject` and returns whether they are consideren unequal.
        This is the opposite of the :func:`__eq__` method.
