from skillbridge.client.extract import parse_all_function, Function


def test_parse_all():
    functions = parse_all_function()
    assert functions

    assert all(isinstance(func, Function) for func in functions)
