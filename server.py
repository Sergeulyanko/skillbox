"""
Серверное приложение для соединений
"""
import asyncio
from asyncio import transports
from typing import Optional

class ClientProtocol(asyncio.Protocol):
    login: str
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server
        self.login = None

    def data_received(self, data: bytes):
        decoded = data.decode()
        print(decoded)

        if self.login is None:
            if decoded.startswith("login:"):
                new_login = decoded.replace("login:", "").replace("\r\n","")
                # ДЗ Serge Ulyanko если логин существует, то сообщаем об этом и отключаем
                for client in self.server.clients:
                    if client.login == new_login:
                        self.transport.write(f"Логин {new_login} занят, попробуйте другой".encode())
                        self.transport.close()
                        break
                else:
                    self.login = new_login
                    self.transport.write(
                    f"Привет, {self.login}!".encode()
                    )
                    # ДЗ Serge Ulyanko при успешном подключении выводим 10 сообщений чата если они есть
                    self.send_history()
        else:
            self.send_message(decoded)

    def send_history(self):
        for str_history in self.server.history_storage:
            self.transport.write(f"History: {str_history}\n".encode())


    def send_message(self, message):
        format_string = f"<{self.login}> {message}"
        encoded = format_string.encode()
        for client in self.server.clients:
            if client.login != self.login:
                client.transport.write(encoded)
        # Сохраняем историю в список, ограничим 10 собщениями
        if (len(self.server.history_storage) >=10):
            # Если размер списка больше 10, то первый элемент удаляем
            self.server.history_storage.pop(0)
        # Добавляем историю в конец списка
        self.server.history_storage.append(format_string)


    def connection_made(self, transport: transports.BaseTransport):
        self.transport = transport
        self.server.clients.append(self)
        print("Соединение установлено")

    def connection_lost(self, exc: Optional[Exception]):
        self.server.clients.remove(self)
        print("Соединение разорвано")



class Server:
    clients: list
    history_storage: list

    def __init__(self):
        self.clients = []
        self.history_storage = []

    def create_protocol(self):
        return ClientProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.create_protocol,
            "127.0.0.1",
            8888
        )
        print("Сервер запущен...")

        await coroutine.serve_forever()

process = Server()
try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")