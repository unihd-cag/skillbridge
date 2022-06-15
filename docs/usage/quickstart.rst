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

    skillbridge path


Read more about :ref:`server`.

Optional One-time setup
-----------------------

You can generate a static completion stub file. That is useful
for IDEs like PyCharm. Type this once into a terminal after you started the
server.

.. code-block:: sh

    skillbridge generate


.. note::

    Generating the static completion stub files requires a tool called ``stubgen``.
    You can install it alongside the python static type check ``mypy`` by typing
    ``pip install mypy`` into your shell.


Connecting to the Server
------------------------


.. code-block:: python

    from skillbridge import Workspace

    ws = Workspace.open()

Here are some :ref:`basic`.


Direct mode without a Server
----------------------------

It is possible to use the skillbridge without an
intermediate server. This is useful, if the script is called directly from Virtuoso.

.. code-block:: python

    from skillbridge import Workspace

    ws = Workspace.open(direct=True)
    print("cell view:", ws.ge.get_edit_cell_view())

Then you can execute the python file from the CIW.

.. code-block:: lisp

    pyRunScript "pathToScript.py"

You can also specify a different python executable

.. code-block:: lisp

    pyRunScript "pathToScript.py" ?python "python3.9"

And you can pass CLI arguments to the script

.. code-block:: lisp

    pyRunScript "pathToScript.py" ?args list("first" "second" "third")

.. note::

    The direct mode will only be enabled if stdin is *not* a TTY. This is the case when the
    script is called from Virtuoso using ``ipcBeginProcess``.

    You can simulate this behaviour by piping text into stdin

    ```
    echo 1234 | python file.py
    ```

    If used with the above code, this will print "geGetEditCellView()" to *stdout* and
    "cell view: 1234" to *stderr*.
