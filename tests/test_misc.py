from subprocess import check_output
from os.path import exists

from pytest import raises

from skillbridge.client.channel import Channel


def test_reports_skill_server_correctly():
    out = check_output('python -m skillbridge'.split())
    assert exists(out.strip())


def test_cannot_use_abc():
    with raises(NotImplementedError):
        Channel(1).send('')

    with raises(NotImplementedError):
        Channel(1).close()

    with raises(NotImplementedError):
        Channel(1).flush()
