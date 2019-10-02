.. _multiple:

Managing Multiple Virtuoso Instances
====================================

You can run multiple Virtuoso instances and have a running server inside
each of them. However, in order to match the clients and server correctly
you must start and connect a bit differently:

**Virtuoso Instance 1**

.. code-block::
    lisp

    ; This starts the server with the default id
    load("PATH-TO-IPC-SERVER")
    pyStartServer


**Python Client 1**

.. code-block::
    python

    ws = Workspace.open()

**Virtuoso Instance 2**

.. code-block::
    lisp

    ; This starts the server with a custom id
    load("PATH-TO-IPC-SERVER")
    pyStartServer "some-id"

**Python Client 2**

.. code-block::
    python

    ws = Workspace.open('some-id')

You could even open both Workspaces in a single python session, but it
is not possible to run two python servers in a single Virtuoso session.