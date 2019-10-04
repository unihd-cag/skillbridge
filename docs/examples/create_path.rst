.. _create_path:

Create some paths on Metal 1 and 2
==============

In this example horizontal and vercital paths are created on Metal1 and Metal2 drawing.

.. code-block:: python 

    from skillbridge import Workspace
    from collections import Counter
    from matplotlib.pyplot import pie,figure,title
    
    
    # Workspace.fix_completion() #use this function for correct tab completion in jupyter-notebook
    
    ws = Workspace.open()
    
    cv = ws.db.open_cell_view_by_type("LIB", "Cell", "layout", "maskLayout", "a")

    for n in range(40):
        ws.rod.create_path(layer=["Metal2", "drawing"], width=0.08, pts = [[0. + 0.125 * n, 0.], [0. + 0.125 * n, 5.]])
        ws.rod.create_path(layer=["Metal2", "drawing"], width=0.08, pts = [[0., 0. + 0.125 * n], [5., 0. + 0.125 * n]])

