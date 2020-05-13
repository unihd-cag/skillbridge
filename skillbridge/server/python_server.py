from os import unlink
from socketserver import StreamRequestHandler, ThreadingMixIn, BaseServer
from socketserver import BaseRequestHandler
from logging import getLogger, basicConfig, WARNING
from sys import stdout, stdin, argv, platform, stderr
from select import select
from typing import Iterable, Optional, Type
from argparse import ArgumentParser

import logging

LOG_FILE = __file__ + '.log'
LOG_FORMAT = '%(asctime)s %(levelname)s %(message)s'
LOG_DATE_FORMAT = '%d.%m.%Y %H:%M:%S'
LOG_LEVEL = WARNING

basicConfig(filename=LOG_FILE, format=LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
logger = getLogger("python-server")


def send_to_skill(data: str) -> None:
    stdout.write(data)
    stdout.write("\n")
    stdout.flush()


def read_from_skill(timeout: Optional[float]) -> str:
    readable = data_ready(timeout)

    if readable:
        return stdin.readline()

    logger.debug("timeout")
    return 'failure <timeout>'


def create_windows_server_class(single: bool) -> Type[BaseServer]:
    from socketserver import TCPServer

    class SingleWindowsServer(TCPServer):
        request_queue_size = 0
        allow_reuse_address = True

        def __init__(self, port: int, handler: Type[BaseRequestHandler]) -> None:
            super().__init__(('localhost', port), handler)

        def server_bind(self) -> None:
            try:
                from socket import SIO_LOOPBACK_FAST_PATH  # type: ignore

                self.socket.ioctl(SIO_LOOPBACK_FAST_PATH, True)
            except ImportError:
                pass
            super().server_bind()

    class ThreadingWindowsServer(ThreadingMixIn, SingleWindowsServer):
        pass

    return SingleWindowsServer if single else ThreadingWindowsServer


def data_windows_ready(timeout: Optional[float]) -> bool:
    return True


def create_unix_server_class(single: bool) -> Type[BaseServer]:
    from socketserver import UnixStreamServer

    class SingleUnixServer(UnixStreamServer):
        request_queue_size = 0
        allow_reuse_address = True

        def __init__(self, file: str, handler: Type[BaseRequestHandler]) -> None:
            self.path = f'/tmp/skill-server-{file}.sock'
            try:
                unlink(self.path)
            except FileNotFoundError:
                pass
            super().__init__(self.path, handler)

    class ThreadingUnixServer(ThreadingMixIn, SingleUnixServer):
        pass

    return SingleUnixServer if single else ThreadingUnixServer


def data_unix_ready(timeout: Optional[float]) -> bool:
    readable, _, _ = select([stdin], [], [], timeout)

    return bool(readable)


if platform == 'win32':
    data_ready = data_windows_ready
    create_server_class = create_windows_server_class
else:
    create_server_class = create_unix_server_class
    data_ready = data_unix_ready


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
        logger.info("got data {}".format(command[:1000].decode()))

        send_to_skill(command.decode())
        logger.info("sent data to skill")
        result = read_from_skill(self.server.skill_timeout).encode()  # type: ignore
        logger.info("got response from skill {!r}".format(result[:1000]))

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


def main(id: str, log_level: str, notify: bool, single: bool, timeout: Optional[float]) -> None:
    logger.setLevel(getattr(logging, log_level))

    server_class = create_server_class(single)

    with server_class(id, Handler) as server:
        server.skill_timeout: Optional[float] = timeout  # type: ignore
        logger.info(
            f"starting server id={id} log={log_level} notify={notify} "
            f"single={single} timeout={timeout}"
        )
        if notify:
            send_to_skill('running')
        server.serve_forever()


if __name__ == '__main__':
    log_levels = "DEBUG WARNING INFO ERROR CRITICAL FATAL".split()
    argument_parser = ArgumentParser(argv[0])
    if platform == 'win32':
        argument_parser.add_argument('id', type=int)
    else:
        argument_parser.add_argument('id')
    argument_parser.add_argument('log_level', choices=log_levels)
    argument_parser.add_argument('--notify', action='store_true')
    argument_parser.add_argument('--single', action='store_true')
    argument_parser.add_argument('--timeout', type=float, default=None)

    ns = argument_parser.parse_args()

    if platform == 'win32' and ns.timeout is not None:
        print("Timeout is not possible on Windows", file=stderr)
        exit(1)

    try:
        main(ns.id, ns.log_level, ns.notify, ns.single, ns.timeout)
    except KeyboardInterrupt:
        pass
