from socketserver import UnixStreamServer, StreamRequestHandler, ThreadingMixIn
from logging import getLogger, basicConfig, WARNING
from sys import stdout, stdin, argv
from select import select
from os import unlink, getenv
from typing import List, Iterable

import logging

LOG_FILE = __file__ + '.log'
LOG_FORMAT = '%(asctime)s %(message)s'
LOG_DATE_FORMAT = '%d.%m.%Y %H:%M:%S'
LOG_LEVEL = WARNING

SOCKET_FILE = '/tmp/skill-server.sock'
TEST_SOCKET_FILE = '/tmp/skill-server-test.sock'

level = getenv('LOG_LEVEL', 'WARNING')
level = getattr(logging, level, WARNING)

basicConfig(filename=LOG_FILE, format=LOG_FORMAT, level=level, datefmt=LOG_DATE_FORMAT)
logger = getLogger("python-server")


def send_to_skill(data: str) -> None:
    stdout.write(data)
    stdout.write("\n")
    stdout.flush()


def read_from_skill() -> str:
    readable, _, _ = select([stdin], [], [], 5)

    if readable:
        return stdin.readline()

    return 'failure <timeout>'


class UnixServer(ThreadingMixIn, UnixStreamServer):
    allow_reuse_address = True


class Handler(StreamRequestHandler):
    def receive_all(self, remaining: int) -> Iterable[bytes]:
        while remaining:
            data = self.request.recv(remaining)
            remaining -= len(data)
            yield data

    def handle_one_request(self) -> bool:
        length = self.request.recv(10)
        if not length:
            logger.warning("client {} lost connection".format(self.client_address))
            return False
        logger.info("got length {}".format(length))

        length = int(length)
        command = b''.join(self.receive_all(length))

        logger.info("received {} bytes".format(len(command)))

        if command.startswith(b'close'):
            logger.info("client {} disconnected".format(self.client_address))
            return False
        logger.info("got data {}".format(command[:1000]))

        send_to_skill(command.decode())
        logger.info("sent data to skill")
        result = read_from_skill().encode()
        logger.info("got response form skill {!r}".format(result[:1000]))

        self.request.send('{:10}'.format(len(result)).encode())
        self.request.send(result)
        logger.info("sent response to client")

        return True

    def try_handle_one_request(self) -> bool:
        try:
            return self.handle_one_request()
        except Exception as e:
            logger.exception(e)
            return False

    def handle(self) -> None:
        logger.info("client {} connected".format(self.client_address))
        client_is_connected = True
        while client_is_connected:
            client_is_connected = self.try_handle_one_request()
            logger.info("loop continue?")
        logger.info("loop ended")


def main(args: List[str]) -> None:
    testmode = len(args) == 2 and args[1] == 'testmode'
    socket_file = TEST_SOCKET_FILE if testmode else SOCKET_FILE

    try:
        unlink(socket_file)
    except FileNotFoundError:
        pass

    with UnixServer(socket_file, Handler) as server:  # type: ignore
        logger.info("starting server")
        if testmode:
            send_to_skill('running')
        server.serve_forever()


if __name__ == '__main__':
    main(argv)
