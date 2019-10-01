from skillbridge.client.extract import parse_all_function, functions_by_prefix,\
    Function, WHITELIST


def test_parse_all():
    functions = parse_all_function()
    assert functions

    assert all(isinstance(func, Function) for func in functions)


def test_by_prefix():
    groups = functions_by_prefix()

    for group in WHITELIST:
        assert group in groups

        assert all(isinstance(func, Function) for func in groups[group])


def test_aliases_are_mapped_even_when_prefix_not_whitelisted():
    functions = functions_by_prefix()['get']

    assert any(func.name == 'getCurrentWindow' for func in functions)


def test_not_whitelisted_prefix_not_present():
    functions = functions_by_prefix()['get']

    assert all(func.name != 'getValue' for func in functions)
