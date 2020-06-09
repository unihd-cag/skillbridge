.. _create_path:

Create some paths 
=================

In this example horizontal and vertical paths are created on Metal1 and Metal2 drawing.

.. code-block:: python 

    from skillbridge import Workspace

    
    ws = Workspace.open()
    
    cv = ws.db.open_cell_view_by_type("LIB", "Cell", "layout", "maskLayout", "a")

    for n in range(40):
        ws.rod.create_path(cv_id=cv, layer=["Metal2", "drawing"], width=0.08, pts=[[0.125 * n, 0], [0.125 * n, 5]])
        ws.rod.create_path(cv_id=cv, layer=["Metal2", "drawing"], width=0.08, pts=[[0, 0.125 * n], [5, 0.125 * n]])
    
    # Redraw the layout window
    ws.hi.redraw()
