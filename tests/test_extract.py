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
