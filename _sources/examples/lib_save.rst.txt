.. _lib_save:

Check/Save Libs
===============

This examples checks and saves all schematic cell_views in a Lib

.. code-block:: python 

    from skillbridge import Workspace

    ws = Workspace.open()

    libs = ws.dd.get_lib_list()
    lib_names = [lib.name for lib in libs]
    # create whitelist
    lib_list = ["LIB0", "LIB1", "LIB2"]

    for lib_name in lib_names:
        if lib_name in lib_list:
            lib = ws.dd.get_obj(lib_name)

            for cell in lib.cells:
                # only if schematic view exists
                if "schematic" in [cell_type.name for cell_type in cell.views]:
                    print("Saved " + cell.name + " !")
                    cv = ws.db.open_cell_view_by_type(lib.name, cell.name, "schematic", "", "a")
                    ws.db.check(cv)
                    ws.db.save(cv)
