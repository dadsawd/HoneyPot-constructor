# honeypots/medium_interaction.py
import asyncio
import paramiko
from io import StringIO
import json
from datetime import datetime
import logging

logging.basicConfig(filename='logs/medium_interaction.log', level=logging.INFO)


class FakeSSHServer(paramiko.ServerInterface):
    """SSH сервер с эмулированием команд"""

    def __init__(self, client_ip):
        self.client_ip = client_ip
        self.logged_in = False
        self.username = None
        self.fake_filesystem = {
            '/': ['bin', 'etc', 'home', 'root', 'var', 'tmp'],
            '/home': ['user', 'admin'],
            '/etc': ['passwd', 'shadow', 'hosts'],
            '/var/www': ['index.html', 'config.php', 'database.sql'],
        }
        self.fake_processes = [
            "sshd",
            "apache2",
            "mysql",
            "postgres",
            "redis-server",
        ]

    def check_auth_password(self, username, password):
        """Логируем попытки входа"""
        log_data = {
            'event': 'ssh_auth_attempt',
            'timestamp': datetime.now().isoformat(),
            'source_ip': self.client_ip,
            'username': username,
            'password': password,
        }
        logging.info(json.dumps(log_data))

        # Приём только определённых пользователей для эмуляции
        if username in ['root', 'admin', 'user']:
            self.logged_in = True
            self.username = username
            return paramiko.AUTH_SUCCESSFUL

        return paramiko.AUTH_FAILED

    def check_channel_request(self, kind, chanid):
        return paramiko.OPEN_SUCCEEDED

    def get_allowed_auths(self, username):
        return 'password'


class MediumInteractionSSH:
    """Эмулятор SSH с базовыми командами"""

    def __init__(self, port=2222):
        self.port = port
        self.host_key = paramiko.RSAKey.generate(1024)

    async def handle_client(self, client, addr):
        """Обработка SSH клиента"""
        transport = paramiko.Transport(client)
        transport.add_server_key(self.host_key)

        server = FakeSSHServer(addr[0])
        transport.start_server(server=server)

        # Открываем канал
        channel = transport.accept(20)
        if channel is None:
            transport.close()
            return

        # Эмулируем shell
        channel.send(f"Linux {self.get_fake_hostname()} 5.10.0-8-generic #1 SMP Debian 5.10.46-5\n")
        channel.send(f"{server.username}@{self.get_fake_hostname()}:~$ ")

        while True:
            try:
                command = channel.recv(1024).decode('utf-8').strip()
                if not command:
                    continue

                response = self.execute_fake_command(server, command)
                channel.send(response)
                channel.send(f"{server.username}@{self.get_fake_hostname()}:~$ ")

                # Логируем команду
                logging.info(json.dumps({
                    'event': 'ssh_command',
                    'ip': addr[0],
                    'user': server.username,
                    'command': command,
                    'timestamp': datetime.now().isoformat(),
                }))

            except Exception as e:
                break

        transport.close()

    def execute_fake_command(self, server, command):
        """Эмулирует выполнение команд Linux"""

        cmd = command.split()[0] if command else ""

        # ls
        if cmd == 'ls':
            cwd = '/'
            files = server.fake_filesystem.get(cwd, [])
            return '\n'.join(files) + '\n'

        # pwd
        elif cmd == 'pwd':
            return '/home/user\n'

        # whoami
        elif cmd == 'whoami':
            return f'{server.username}\n'

        # cat /etc/passwd
        elif cmd == 'cat':
            if 'passwd' in command:
                return "root:x:0:0:root:/root:/bin/bash\nuser:x:1000:1000:user:/home/user:/bin/bash\n"
            return "cat: file not found\n"

        # ps
        elif cmd == 'ps':
            return '\n'.join([f"PID  COMMAND\n1    sshd"] +
                             [f"{i + 100}  {p}" for i, p in enumerate(server.fake_processes)]) + '\n'

        # uname
        elif cmd == 'uname':
            return "Linux\n"

        # id
        elif cmd == 'id':
            return f"uid=1000({server.username}) gid=1000({server.username}) groups=1000({server.username})\n"

        # sudo (логируем)
        elif cmd == 'sudo':
            logging.warning(json.dumps({
                'event': 'privilege_escalation_attempt',
                'command': command,
                'ip': server.client_ip,
            }))
            return "sudo: command not found\n"

        # Неизвестная команда
        else:
            return f"bash: {cmd}: command not found\n"

    @staticmethod
    def get_fake_hostname():
        return "web-server"

    async def start(self):
        """Запуск SSH honeypot сервера"""
        print(f"[*] SSH Medium-interaction honeypot listening on port {self.port}")

        server = await asyncio.start_server(
            self.handle_client,
            '0.0.0.0',
            self.port
        )

        async with server:
            await server.serve_forever()


# Запуск
if __name__ == "__main__":
    ssh_trap = MediumInteractionSSH(port=2222)
    asyncio.run(ssh_trap.start())