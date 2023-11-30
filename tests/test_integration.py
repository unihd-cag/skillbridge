from pathlib import Path
from time import sleep
from warnings import warn

from pytest import fixture, raises, skip

from skillbridge import LazyList, RemoteObject, RemoteTable, SkillCode, Symbol, Var, Workspace

here = Path(__file__).parent


@fixture(scope='module')
def ws() -> Workspace:
    try:
        workspace = Workspace.open()
        assert workspace['plus'](1, 2) == 3
    except (Exception, ValueError, AssertionError):
        warn("Skipping integration tests, because Workspace could not connect", UserWarning)
        skip()

    return workspace


def test_can_add_two_numbers(ws: Workspace) -> None:
    assert ws['plus'](2, 3) == 5


def test_can_create_a_hash_table(ws: Workspace) -> None:
    t = ws.make_table('T')

    assert isinstance(t, RemoteTable)
    assert str(t) == "<remote table:T>"


def test_can_store_keys_in_hash_table(ws: Workspace) -> None:
    t = ws.make_table('T')

    t['x'] = 123
    t[123] = [2, 3, 4]

    assert t['x'] == 123
    assert t[123] == [2, 3, 4]


def test_can_read_length_of_hash_table(ws: Workspace) -> None:
    t = ws.make_table('T')

    assert len(t) == 0
    t['x'] = 1
    assert len(t) == 1
    t['x'] = 2
    assert len(t) == 1
    del t['x']
    assert len(t) == 0


def test_can_iterate_over_hash_table_keys(ws: Workspace) -> None:
    t = ws.make_table('T')

    assert list(t) == []
    t['x'] = 1
    assert list(t) == ['x']
    t[2] = 3
    assert list(t) == ['x', 2]


def test_can_use_hash_table_like_a_dict(ws: Workspace) -> None:
    t = ws.make_table('T')

    assert dict(t) == {}
    t['x'] = 1
    assert dict(t) == {'x': 1}
    t.update(y=3)
    assert dict(t) == {'x': 1, 'y': 3}


def test_can_use_symbol_keys_in_hash_table(ws: Workspace) -> None:
    t = ws.make_table('T', None)

    t[Symbol('key')] = 123
    assert t['key'] is None
    assert t[Symbol('key')] == 123


def test_missing_key_raises_key_error(ws: Workspace) -> None:
    t = ws.make_table('T')

    with raises(KeyError, match=r'XYZ'):
        _ = t['XYZ']


def test_open_file(ws: Workspace) -> None:
    file = ws['outfile']('__test_skill_python.txt', 'w')

    assert file.skill_parent_type == 'openfile'
    assert file.skill_type == 'open_file'
    assert str(file).startswith('<remote open_file')
    assert isinstance(dir(file), list)


def test_remote_object(ws: Workspace) -> None:
    libs = ws.dd.get_lib_list()

    assert libs
    lib = libs[0]

    assert isinstance(lib.skill_id, int)
    assert lib.skill_parent_type == 'dd'
    assert lib.skill_type == 'Lib'
    assert str(lib).startswith('<remote Lib@')
    assert set(dir(lib)) > {'cells', 'is_readable', 'group', 'name'}
    assert lib.is_readable == lib['isReadable']

    with raises(AttributeError):
        _ = lib._repr_html_

    lib.getdoc()

    assert lib == lib  # noqa: PLR0124
    assert lib != libs[1]
    assert not (lib == 1)  # noqa: SIM201  # this tests __eq__ and the next line tests __ne__
    assert lib != 1


def _lib_with_cells(ws: Workspace) -> RemoteObject:
    return max(ws.dd.get_lib_list(), key=lambda lib: len(lib.cells or ()))


def test_lazy_list(ws: Workspace) -> None:
    lib = _lib_with_cells(ws)

    cells = lib.lazy.cells

    assert isinstance(lib.cells, list)
    assert isinstance(cells, LazyList)
    assert str(cells).startswith('<lazy list')

    assert cells.filter() is cells
    assert len(cells) > 0
    assert len(cells.filter(name="__no_cell_is_named_this")) == 0

    assert cells[0] == lib.cells[0]
    assert cells[:] == lib.cells

    with raises(RuntimeError):
        _ = cells[1:2:3]

    names = ws.make_table('CellNames')

    cells.foreach(ws['setarray'], names, LazyList.arg['name'], LazyList.arg['readPath'])

    for cell in [cells[0], cells[1], cells[2]]:
        if cell is None:
            continue

        assert names[cell.name] == cell.read_path

    with raises(RuntimeError):
        cells.foreach(SkillCode('setarray'), names, LazyList.arg)

    cells.foreach(SkillCode('print(123)'))

    read_write = cells.filter(is_readable=True, is_writable=True)
    read_only = cells.filter(is_readable=True, is_writable=False)
    write_only = cells.filter(is_readable=False, is_writable=True)
    nothing = cells.filter(is_readable=False, is_writable=False)
    assert len(cells) == len(read_only) + len(read_write) + len(write_only) + len(nothing)


def test_vector_without_default(ws: Workspace) -> None:
    v = ws.make_vector(10)

    assert len(v) == 10

    for i in range(-7, 14):
        with raises(IndexError, match=str(i)):
            _ = v[i]

    v[0] = 10
    v[2] = 12

    assert list(v) == [10]
    v[1] = 11
    assert list(v) == [10, 11, 12]

    assert v[0] == 10

    with raises(IndexError, match='10'):
        v[10] = 100


def test_direct_globals(ws: Workspace) -> None:
    ws['set'](Symbol('myGlobalValue'), 102030)

    assert ws.__.my_global_value == 102030
    assert ws.__['myGlobalValue'] == 102030


def test_collections_with_default(ws: Workspace) -> None:
    t = ws.make_table('T', 123)
    assert t[10] == 123

    v = ws.make_vector(10, 12)
    assert list(v) == [12] * 10


def test_table_getattr_is_equivalent_to_symbol_lookup(ws: Workspace) -> None:
    t = ws.make_table('T')

    t[Symbol('abcDef')] = 10
    assert t.abc_def == 10

    t.xyz_abc = 20
    assert t[Symbol('xyzAbc')] == 20


def test_nil_t_nil_is_not_a_disembodied_property_list(ws: Workspace) -> None:
    assert ws["cdr"]([0, None, True, None]) == [None, True, None]


def test_run_script_does_not_block(ws: Workspace) -> None:
    variable = 'skillbridge_script_args'
    ws['set'](Symbol(variable), 0)
    assert ws['pyRunScript'](str(here / 'script.py'), args=(variable, '42', '0.25'))

    assert ws['plus'](Var(variable), 1) == 1
    sleep(1.0)
    assert ws['plus'](Var(variable), 1) == 43


def test_run_script_blocks_when_requested(ws: Workspace) -> None:
    variable = 'skillbridge_script_args'
    ws['set'](Symbol(variable), 0)
    assert ws['pyRunScript'](str(here / 'script.py'), args=(variable, '42', '0.25'), block=True)

    assert ws['plus'](Var(variable), 1) == 43


def test_form_vectors_have_dir(ws: Workspace) -> None:
    form = ws.hi.get_current_form()
    assert 'button_layout' in dir(form)


def test_form_vectors_have_getattr(ws: Workspace) -> None:
    form = ws.hi.get_current_form()
    assert isinstance(form.button_layout, list)
