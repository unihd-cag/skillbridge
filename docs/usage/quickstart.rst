.. _quickstart:

Quickstart
==========

Starting the Server
-------------------

Open the Skill console in Virtuoso and type

.. code-block:: lisp

    load("PATH-TO-SKILL-IPC-SCRIPT")
    pyStartServer

You can obtain the correct path from the python library like this:

.. code-block:: sh

    python -m skillbridge


Read more about :ref:`server`.

Connecting to the Server
------------------------


.. code-block:: python

    from skillbridge import Workspace

    ws = Workspace.open()

Here are some :ref:`basic`.