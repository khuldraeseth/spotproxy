import threading
import socket
from settings import WIREGUARD_CONFIG_LOCATION
import psutil
from time import sleep
import json
from logger import log

client_addresses = []
client_sockets = []
nat_sockets = []


class ForwardThread(threading.Thread):
    def __init__(
        self,
        source_socket: socket.socket,
        destination_socket: socket.socket,
        description: str,
    ):
        threading.Thread.__init__(self)
        self.source_socket = source_socket
        self.destination_socket = destination_socket
        self.description = description

    def run(self):
        with self.source_socket, self.destination_socket:
            while data := self.source_socket.recv(1024):
                self.destination_socket.sendall(data)

        # data = " "
        # try:
        #     while data:
        #         data = self.source_socket.recv(1024)
        #         if data:
        #             self.destination_socket.sendall(data)
        #         else:
        #             try:
        #                 self.source_socket.close()
        #                 self.destination_socket.close()
        #             except:
        #                 # log('connection closed')
        #                 break
        # except:
        #     # log('connection closed')
        #     try:
        #         self.source_socket.close()
        #     except:
        #         pass
        #     try:
        #         self.destination_socket.close()
        #     except:
        #         pass


class ForwardingServerThread(threading.Thread):
    def __init__(self, listen_endpoint: tuple, forward_endpoint: tuple):
        threading.Thread.__init__(self)

        self.listen_endpoint = listen_endpoint
        self.forward_endpoint = forward_endpoint

    def run(self):
        global client_addresses, client_sockets, nat_sockets
        try:
            dock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            dock_socket.bind(self.listen_endpoint)
            dock_socket.listen(5)
            while True:
                client_socket, client_address = dock_socket.accept()
                if client_address not in client_addresses:
                    client_addresses.append(client_address)
                    client_sockets.append(client_socket)

                if len(client_addresses) % 10 == 0:
                    print(len(client_addresses))
                nat_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                nat_socket.connect(self.forward_endpoint)
                nat_sockets.append(nat_socket)
                way1 = ForwardThread(
                    client_socket, nat_socket, "client -> server"
                )
                way2 = ForwardThread(
                    nat_socket, client_socket, "server -> client"
                )
                way1.start()
                way2.start()
        except Exception as e:
            print("ERROR: a fatal error has happened")
            print(str(e))


class MigratingAgent(threading.Thread):
    def __init__(self, client_socket: socket.socket):
        super.__init__(self)
        self.client_socket = client_socket

    def run(self):
        full_file_data = b""
        while data := self.client_socket.recv(1024):
            full_file_data += data
        self.client_socket.shutdown(socket.SHUT_RD)

        config = json.loads(full_file_data)
        if config.inbounds.settings.clients == []:
            log("ERROR: Migrated data was empty!")
            return

        # TODO figure out what's going on with the wg public_key here
        # probably not needed with v2ray? but we might run into encryption
        # problems later :(

        with open(WIREGUARD_CONFIG_LOCATION, "a") as f:
            json.dump(config, f)


class MigrationHandler(threading.Thread):
    def __init__(self, listen_endpoint: tuple):
        threading.Thread.__init__(self)
        self.listen_endpoint = listen_endpoint

    def run(self):
        try:
            dock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            dock_socket.bind(self.listen_endpoint)
            dock_socket.listen(5)

            while True:
                client_socket, client_address = dock_socket.accept()
                agent = MigratingAgent(client_socket)
                agent.start()
        finally:
            dock_socket.close()
            new_server = MigrationHandler(self.listen_endpoint)
            new_server.start()


def calculate_network_throughput(interval=0.01):
    net_io_before = psutil.net_io_counters()
    sleep(interval)
    net_io_after = psutil.net_io_counters()
    sent_throughput = (
        net_io_after.bytes_sent - net_io_before.bytes_sent
    ) / interval

    return sent_throughput


class PollingHandler(threading.Thread):
    def __init__(self, listen_endpoint: tuple):
        threading.Thread.__init__(self)
        self.listen_endpoint = listen_endpoint

    def run(self):
        try:
            dock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            dock_socket.bind(self.listen_endpoint)
            dock_socket.listen(5)

            while True:
                poller_socket, poller_address = dock_socket.accept()
                data = poller_socket.recv(1024)  # noqa

                cpu_utilization = psutil.cpu_percent(interval=0.01)
                throughput = calculate_network_throughput()
                report = {}
                report["utility"] = cpu_utilization
                report["throughput"] = throughput
                report["connected_clients"] = client_addresses

                message_to_send = json.dumps(report)
                poller_socket.sendall(message_to_send.encode())
                poller_socket.close()

        finally:
            dock_socket.close()
            new_server = PollingHandler(self.listen_endpoint)
            new_server.start()
