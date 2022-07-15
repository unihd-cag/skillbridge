.. _raw:

Disable camelCase translation
=============================


Sometimes it is useful to disable the automatic translation
from snake_case to camelCase when accessing attributes.

.. code-block:: python
   
   from skillbrige import Workspace

   ws = Workspace.open()
   thing = ws.prefix.some_function_that_returns_an_object()

   print(thing.snake_case)
   # this translates to thing->snakeCase

   print(thing['snake_case'])
   # this translates to thing->snake_case

