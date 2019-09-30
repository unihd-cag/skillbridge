Communication Protocol
======================

.. figure:: /images/components.svg

    The different components of the Skill Bridge

The block diagram shows two important communication interfaces.
namely, the TCP/Unix socket interface between the client library
and the python server and the IPC interface between the skill script and the python server.

The IPC protocol
----------------

The skill script communicated via ``stdin`` and ``stdout`` with the python server. All
messages are initiated by the python server (called *question*) which is followed by
exactly one *answer* from the skill. All *questions* and *answers* are terminated by
a newline character ``\n``.

The Question
~~~~~~~~~~~~

A *question* consists a single line containing executable skill code. See the following examples:

.. code-block::
    lisp

    "1 + 2\n"

    "geGetEditCellView()\n"

    "__py_cell = geGetEditCellView()\n"

The Answer
~~~~~~~~~~

An *answer* consists of the execution status, either ``"failure"`` or ``"success"``,
and the result itself. The result is exactly the string representation given by skill.

Examples:

.. code::
    lisp

    "success 1\n"

    "success (1 2 3)\n"

    "success db:0x1234\n"

    "failure error ...\n"

.. figure:: /images/diagrams-question-answer.svg

    Sequence diagram for the question and answer protocol


Behaviour
~~~~~~~~~

The skill script waits for *questions*. When it receives one it executes the code.
In case of an error it sends an *answer* beginning with ``"failure"`` followed by the
error message. Otherwise it sends an *answer* beginning with ``"success"`` followed by
the string representation of the result.

The python server waits one minute after it sent a *question*. It it does not receive
an *answer* in that time it automatically assumes the following *answer*:
``"failure <timeout>"``.


Test Mode
~~~~~~~~~

There is one exception to the protocol above. If the server is started with the ``-notify``
option it will send a single message containing "running\n" via stdout. This message
must not be executed as skill code. Its sole purpose is to notify the parent process
that the server is running.

The Socket Protocol
-------------------

This protocol is similar to the IPC protocol. The difference is the way single messages are
grouped together. As TCP has no concept of messages, the length of the message is sent first,
followed by the message itself. As the length of the length can also vary, it is fixed to
exactly 10 digits. Smaller lengths must be padded with either zeros or spaces.

See the following examples:

>>> encode("1 + 2")
b'00000000051 + 2'

>>> encode("__py_cell = geGetEditCellView()")
b'0000000031__py_cell = geGetEditCellView()'

.. figure:: /images/diagrams-socket.svg

    Sequence diagram for the socket protocol


A Full Roundtrip
----------------

.. figure:: /images/diagrams-flow.svg

    A full roundtrip of a single python expression