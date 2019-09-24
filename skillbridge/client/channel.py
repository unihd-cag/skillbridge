from socket import socket, SOCK_STREAM, AF_UNIX
from select import select
from typing import Iterable


class Channel:
    def __init__(self, max_transmission_length: int):
        self._max_transmission_length = max_transmission_length

    def send(self, data: str) -> str:
        raise NotImplementedError

    def close(self) -> None:
        raise NotImplementedError

    def flush(self) -> None:
        raise NotImplementedError

    @property
    def max_transmission_length(self) -> int:
        return self._max_transmission_length

    @max_transmission_length.setter
    def max_transmission_length(self, value: int) -> None:
        self._max_transmission_length = value

    def __del__(self) -> None:
        self.close()


class UnixChannel(Channel):
    address_family = AF_UNIX
    socket_kind = SOCK_STREAM

    def __init__(self, filename: str):
        super().__init__(1_000_000)

        self.connected = False
        self.address = filename
        self.socket = self.connect()

    def connect(self) -> socket:
        s = socket(self.address_family, self.socket_kind)
        s.connect(self.address)
        self.connected = True
        return s

    def reconnect(self) -> None:
        self.socket.close()
        self.socket = self.connect()

    def _receive(self, remaining: int) -> Iterable[bytes]:
        while remaining:
            data = self.socket.recv(remaining)
            remaining -= len(data)
            yield data

    def send(self, data: str) -> str:
        byte = data.encode()

        if len(byte) > self._max_transmission_length:
            got = len(byte)
            should = self._max_transmission_length
            raise ValueError(f'Data exceeds max transmission length {got} > {should}')

        length = '{:10}'.format(len(byte)).encode()
        try:
            self.socket.sendall(length)
        except (BrokenPipeError, OSError):
            print("attempting to reconnect")
            self.reconnect()
            self.socket.sendall(length)

        try:
            self.socket.sendall(byte)
        except (BrokenPipeError, OSError):
            print("attempting to reconnect")
            self.reconnect()
            self.socket.sendall(length)
            self.socket.sendall(byte)
        received_length = int(self.socket.recv(10))
        response = b''.join(self._receive(received_length)).decode()

        status, response = response.split(' ', maxsplit=1)

        if status == 'failure':
            raise RuntimeError(response)
        return response

    def close(self) -> None:
        if self.connected:
            self.socket.sendall(b'         5close')
            self.socket.close()
            self.connected = False

    def flush(self) -> None:
        while True:
            read, _, _ = select([self.socket], [], [], 0.1)
            if read:
                length = int(self.socket.recv(10))
                self.socket.recv(length)
            else:
                break
