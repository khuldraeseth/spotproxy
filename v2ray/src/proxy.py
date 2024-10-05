from server_threads import (
    ForwardingServerThread,
    MigrationHandler,
    PollingHandler,
)
from settings import V2RAY_CONFIG_LOCATION, V2RAY_PORT, MIGRATION_PORT
import requests
from logger import log
from time import time
import socket


def get_public_ip():
    try:
        response = requests.get("https://httpbin.org/ip")
        match response.status_code:
            case 200:
                return response.json()["origin"]
            case n:
                log(f"Failed to retrieve public IP. Status code: {n}")

    except requests.RequestException as e:
        log(f"Request error: {e}")


class Proxy:
    def __init__(
        self,
        v2ray_endpoint,
        nat_endpoint,
        broker_endpoint,
        migration_endpoint,
        polling_endpoint,
    ) -> None:
        """
        endpoints are tuples of: (address, port)
        """
        self.my_number = int(
            socket.gethostbyname(socket.gethostname()).split(".")[-1]
        )
        self.v2ray_endpoint = v2ray_endpoint
        self.nat_endpoint = nat_endpoint
        self.broker_endpoint = broker_endpoint
        self.migration_endpoint = migration_endpoint
        self.polling_endpoint = polling_endpoint

    def migrate(self, new_proxy_ip):
        start_time = time()
        # migrate address
        global client_addresses, client_sockets, nat_sockets
        with open(V2RAY_CONFIG_LOCATION, "rb") as f:
            data = f.read()
        new_proxy_address = new_proxy_ip
        new_proxy_socket = MIGRATION_PORT
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((new_proxy_address, new_proxy_socket))
        s.sendall(data)

        print(f"sending migration notice to {len(client_addresses)} clients")

        for address, cli_sock, dest_sock in zip(
            client_addresses, client_sockets, nat_sockets
        ):
            cli_sock.send("bye!".encode())
            cli_sock.close()
            dest_sock.close()
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((address[0], MIGRATION_PORT))
                s.sendall(f"{new_proxy_address}:{V2RAY_PORT}".encode())
        print("sent to all successfully! GGs.")

        nat_sockets = []
        migration_time = time() - start_time

        data = {"avg": migration_time}

    def run(self):
        ip = get_public_ip()
        print(f"my endpoint is: {ip}:{V2RAY_PORT}")

        forwarding_server = ForwardingServerThread(
            self.wireguard_endpoint, self.nat_endpoint
        )
        migration_handler = MigrationHandler(self.migration_endpoint)
        polling_handler = PollingHandler(self.polling_endpoint)
        polling_handler.start()
        migration_handler.start()
        forwarding_server.start()

        dock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        dock_socket.bind((self.broker_endpoint[0], self.broker_endpoint[1]))
        dock_socket.listen(5)

        while True:
            broker_socket, broker_address = dock_socket.accept()

            data = broker_socket.recv(1024)

            print(f"INFO: got message from {broker_address}: {data.decode()}")

            command = data.decode().strip().lower().split()
            broker_socket.close()

            if command[0] == "migrate":
                if len(command) > 1:
                    self.migrate(command[1])
                else:
                    self.migrate(f"172.17.0.{self.my_number + 1}")
            else:
                print("ERROR: Unknown command. Ignoring...")
