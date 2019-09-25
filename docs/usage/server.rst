.. _server:

The Python Server
=================

Initially the server must be started by loading the ``python_server.il``.

After that, these management commands are available in the Skill console.

.. function:: pyKillServer()

    This terminates the python subprocess and thus, kills the server.
    After that, no connections from the client side can be made anymore
    and active connections will result in a :class:`BrokenPipe` exception
    the next time they are used.

.. function:: pyReloadServer(level="WARNING")

    This calls :func:`pyKillServer` and reloads the ``python_server.il``
    Skill script. With this function you can effectively restart the python
    server in case it crashes.

    The client library will attempt to reconnect, but the success is not guaranteed.

    The ``level`` can be used to set the log level, the default is ``"WARNING"``.
    Other values are ``"DEBUG"`` to print absolutely everything, ``"INFO"``,
    ``"WARNING"``, ``"ERROR"`` and ``"FATAL"``.

    .. warning::

        The loglevels ``"DEBUG"`` and ``"INFO"`` are not recommended, because then
        the time for a round-trip between the client and the server is effectively
        two to three times as long!

.. function:: pyShowLog(numberOfLines=10)

    Used for debugging. This shows the logging output from the
    python server. The parameter ``numberOfLines`` controlls
    how many lines will be printed. It always refers to the **last**
    ``numberOfLines`` lines.

.. function:: pyDumpFunctionDefinitions(filename)

    This dumps all function names, parameters and documentations into the file
    given by ``filename``. These function definitions are used by the python
    module to generate the mapping of the global functions.

    If ``filename`` is set to the special value ``"<install>"`` then the file
    will be placed inside the python module ready to be used. This command
    must be executed once before you can use the python module.
