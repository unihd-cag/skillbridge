.. _logging:

Logging
=======

Skillbridge creates several log files while running. By default they are stored in the 
current working directory where the cadence tool was started. You can override that by setting
the environmental variable ``SKILLBRIDGE_LOG_DIRECTORY`` to a valid folder name **before** starting the cadence tool.

.. warning::

    Do not include the trailing slash when setting the variable!


Alternatively you can also set the variable inside the CIW **before** loading the server script

.. code-block:: lisp

    setShellEnvVar("SKILLBRIDGE_LOG_DIRECTORY" "some/valid/path/here")
    load(...)

The following log files are created:

1. ``skillbridge_server.log`` for the python server (use ``pyStartServer ?logLevel LEVEL`` to control the log level)
2. ``skillbridge_skill.log`` for the skill process.
3. ``skillbridge_script.log`` for the skill process when using ``pyRunScript``
