.. _server:

The Python Server
=================

Initially the server script must be run by loading the ``python_server.il``. (Type ``skillbridge path``
into your terminal to get the correct paths).

.. code-block::
    lisp

    load("PATH-TO-SKILL-IPC-SCRIPT")

After that, these management commands are available in the Skill console.

.. function:: pyStartServer(id="default" logLevel="INFO" singleMode=nil timeout=nil python="python")

    This starts the python server. If you are only running a single instance of
    Virtuoso you can use the default id. For more instances, each server needs its own
    id.

    The ``logLevel`` can be used to set the log level, the default is ``"INFO"``.
    Other values are ``"DEBUG"`` to print absolutely everything, ``"INFO"``,
    ``"WARNING"``, ``"ERROR"`` and ``"FATAL"``.

    .. warning::

        The log levels ``"DEBUG"`` and ``"INFO"`` are not recommended, because then
        the time for a round-trip between the client and the server is effectively
        two to three times as long!

    The ``singleMode`` parameter allows you to disable simultaneous connections to
    the server. By default, multiple connections are allowed for convenience reasons.
    Especially jupyter users will benefit from this, since jupyter keeps the socket
    connections open.

    .. warning::

        Even when ``singleMode`` is disabled it is **never** safe to simultaneously
        access the server. This will lead to strange errors, where variables don't
        contain what you initially assigned to them.

        In order to stay safe: **never** interleave commands from two different
        connections.

    With the ``timeout`` parameter you can control how long the server will wait for
    the Skill code to finish. ``nil`` means: wait forever, setting it to a number will
    wait at most that number as seconds.

    .. warning::

        Whenever a timeout occurs the python client and the Skill server are out of sync.
        You must restart the Skill server before you can continue.

    The default python interpreter that is used to start the server is ``"python"``. If your
    interpreter is called differently (e.g. ``"python3.6"``) you can pass its name with the
    ``python`` parameter. Your specified interpreter does not need the ``skillbridge`` package.
    The only requirement is ``python>=3.6``.

    .. note::

        The parameters are marked with ``@key`` which means that it is only possible
        to change their default value by explicitly naming them when calling the function.

        Here are a few examples:

        .. code-block::
            lisp

            ; only change the log level to "INFO"
            pyStartServer ?logLevel "INFO"

            ; only change the server id to "foo"
            pyStartServer ?id "foo"

            ; change both server id and log level
            pyStartServer ?id "foo" ?logLevel "INFO"

            ; same as above, the order does not matter
            pyStartServer ?logLevel "INFO" ?id "foo"

            ; this tells the server to wait at most 10.5 seconds
            ; before sending a timeout error
            pyStartServer ?timeout 10.5

            ; use a custom interpreter path
            pyStartServer ?python "python3.6"

.. function:: pyKillServer()

    This terminates the python subprocess and thus, kills the server.
    After that, no connections from the client side can be made anymore
    and active connections will result in a :class:`BrokenPipe` exception
    the next time they are used.

.. function:: pyReloadScript()

    This calls :func:`pyKillServer` and reloads the ``python_server.il``
    Skill script. Normally this function would not be used.


.. function:: pyShowLog(numberOfLines=10)

    Used for debugging. This shows the logging output from the
    python server. The parameter ``numberOfLines`` controls
    how many lines will be printed. It always refers to the **last**
    ``numberOfLines`` lines.

    Example:

    .. code-block:: lisp

        ; show the last 10 lines of the log file
        pyShowLog

        ; show the last 20 lines of the log file
        pyShowLog 20
