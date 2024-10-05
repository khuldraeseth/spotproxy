import socket
import threading

from settings import V2RAY_CONFIG_LOCATION, MIGRATION_PORT

from utils import TrafficGetterThread, TrafficMeasurementPythonThread
import subprocess
from time import sleep, time
from struct import unpack
from logger import log
import sys
import json


class MigrationHandler(threading.Thread):
    def __init__(self, listen_endpoint: tuple):
        threading.Thread.__init__(self)
        self.listen_endpoint = listen_endpoint

    def run(self):
        log(
            "==== client migration handler listening on "
            f"{self.listen_endpoint[0]}:{self.listen_endpoint[1]}"
        )
        dock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        dock_socket.bind((self.listen_endpoint[0], self.listen_endpoint[1]))
        dock_socket.listen(5)

        while True:
            mig_socket, mig_address = dock_socket.accept()
            print(
                "==== migration request from "
                f"{mig_address}:{self.listen_endpoint[1]}"
            )

            data = mig_socket.recv(1024)
            log(f"migration info: {data}")
            new_endpoint = data.decode()
            new_endpoint_address, new_endpoint_port = new_endpoint.split(":")
            new_endpoint_port = int(new_endpoint_port)

            new_outbound = {
                "address": new_endpoint_address,
                "port": new_endpoint_port,
                "users": [{"id": "deadbeef-dead-beef-dead-beefdeadbeef"}],
            }

            with open(V2RAY_CONFIG_LOCATION, "rwb") as f:
                config = json.load(f)
                config.outbounds[0].settings.vnext[0] = new_outbound
                json.dump(config, f)

            subprocess.run("pkill v2ray", shell=True)
            subprocess.Popen(
                f"v2ray --config={V2RAY_CONFIG_LOCATION} run", shell=True
            )
            global client_socket, host, port
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((host, port))
            log(f"Connected to {new_endpoint_address}:{new_endpoint_port}")


def tcp_client(host, port):
    try:
        global client_socket
        client_socket.connect((host, port))
        log(f"Connected to {host}:{port}")

        while True:
            message = input("Enter a message (or 'exit' to quit): ")
            if message.lower() == "exit":
                break

            client_socket.send(message.encode("utf-8"))

            data = client_socket.recv(1024)
            log(f"Received from server: {data.decode('utf-8')}")

    except ConnectionRefusedError:
        log(
            "Connection to the server failed. "
            "Make sure the server is running."
        )

    finally:
        client_socket.close()
        log("Connection closed.")


def efficacy_test_bulk_download(host, port, migration, test_duration=300):
    global client_socket
    client_socket.connect((host, port))
    log(f"Connected to {host}:{port}")
    start_time = time()
    measure_thread = TrafficGetterThread(start_time=start_time, duration=300)
    measure_thread.start()
    measure_thread_2 = TrafficMeasurementPythonThread(
        start_time=start_time, duration=test_duration
    )
    measure_thread_2.start()
    i = 0
    amount_of_data_gathered = 0
    while time() - start_time < test_duration:
        try:
            while time() - start_time < test_duration:
                message = f"BEEGMode {amount_of_data_gathered}"
                client_socket.send(message.encode("utf-8"))
                bs = client_socket.recv(8)
                (length,) = unpack(">Q", bs)
                data = b""
                while len(data) < length:
                    to_read = length - len(data)
                    client_socket.settimeout(0.2)
                    new_data = client_socket.recv(
                        4096 if to_read > 4096 else to_read
                    )
                    data += new_data
                    amount_of_data_gathered += len(new_data)

                    if time() - start_time > i * 20:
                        log(f"here at {20*i}s, got {len(data)}data", pr=True)
                        i += 1
                # Note: We might have to add this back later
                # sleep(0.1)
        except ConnectionRefusedError:
            log(
                "Connection to the server failed. "
                "Make sure the server is running."
            )

        except ConnectionResetError:
            log("migrating...")

        except Exception as e:
            log("the pipe is not ready yet, sleeping for 0.01 sec")
            log(f"error: {e}")
            sleep(0.01)
    log(f"test is done, total time was: {time() - start_time} secs")


def efficacy_test_wikipedia(host, port, migration, test_duration=999999):
    global client_socket
    client_socket.connect((host, port))
    log(f"Connected to {host}:{port}")
    start_time = time()
    measure_thread = TrafficGetterThread(
        start_time=start_time, duration=test_duration
    )
    measure_thread.start()
    measure_thread_2 = TrafficMeasurementPythonThread(
        start_time=start_time, duration=test_duration
    )
    measure_thread_2.start()
    # if migration:
    #     testing_migration_senderr = TestingMigrationSenderThread(
    #         start_time=start_time, duration=test_duration
    #     )
    #     testing_migration_senderr.start()
    i = 0
    while time() - start_time < test_duration:
        try:
            while time() - start_time < test_duration:
                message = "https://www.wikipedia.org/"
                client_socket.send(message.encode("utf-8"))
                bs = client_socket.recv(8)
                (length,) = unpack(">Q", bs)
                data = b""
                while len(data) < length:
                    to_read = length - len(data)
                    new_data = client_socket.recv(
                        4096 if to_read > 4096 else to_read
                    )
                    data += new_data

                    if time() - start_time > i * 20:
                        log(f"here at {20*i}s, got {len(data)}data", pr=True)
                        i += 1

                sleep(0.1)
        except ConnectionRefusedError:
            log(
                "Connection to the server failed. "
                "Make sure the server is running."
            )

        except ConnectionResetError:
            log("migrating...")

        except Exception as e:
            log("the pipe is not ready yet, sleeping for 0.01 sec")
            log(f"error: {e}")
            sleep(0.01)
    log(f"test is done, total time was: {time() - start_time} secs", pr=True)


def efficacy_test_kv_store(host, port, migration, test_duration=300):
    global client_socket
    client_socket.connect((host, port))
    log(f"Connected to {host}:{port}")
    start_time = time()
    measure_thread = TrafficGetterThread(
        start_time=start_time, duration=test_duration
    )
    measure_thread.start()
    measure_thread_2 = TrafficMeasurementPythonThread(
        start_time=start_time, duration=test_duration
    )
    measure_thread_2.start()
    i = 0
    while time() - start_time < test_duration:
        try:
            while time() - start_time < test_duration:
                message = "GET testing_key"
                client_socket.send(message.encode("utf-8"))
                bs = client_socket.recv(8)
                (length,) = unpack(">Q", bs)
                data = b""
                while len(data) < length:
                    to_read = length - len(data)
                    new_data = client_socket.recv(
                        4096 if to_read > 4096 else to_read
                    )
                    data += new_data
                    if time() - start_time > i * 20:
                        log(f"here at {20*i}s, got {len(data)}data", pr=True)
                        i += 1

                sleep(0.1)
        except ConnectionRefusedError:
            log(
                "Connection to the server failed. "
                "Make sure the server is running."
            )

        except ConnectionResetError:
            log("migrating...")

        except Exception as e:
            log("the pipe is not ready yet, sleeping for 0.01 sec")
            log(f"error: {e}")
            sleep(0.01)
    log(f"test is done, total time was: {time() - start_time} secs", pr=True)


def mass_test_simple_client(host, port, test_duration=1500):
    global client_socket
    print(f"trying to connect to ({host}, {port})")
    client_socket.connect((host, port))
    log(f"Connected to {host}:{port}", pr=True)
    start_time = time()
    i = 0
    while time() - start_time < test_duration:
        try:
            while time() - start_time < test_duration:
                message = "https://www.wikipedia.org/"
                client_socket.send(message.encode("utf-8"))
                bs = client_socket.recv(8)
                (length,) = unpack(">Q", bs)
                data = b""
                while len(data) < length:
                    to_read = length - len(data)
                    new_data = client_socket.recv(
                        4096 if to_read > 4096 else to_read
                    )
                    data += new_data

                    if time() - start_time > i * 20:
                        log(f"here at {20*i}s, got {len(data)}data", pr=True)
                        i += 1

                sleep(0.5)
        except ConnectionRefusedError:
            log(
                "Connection to the server failed. "
                "Make sure the server is running."
            )

        except ConnectionResetError:
            log("migrating...")

        except Exception as e:
            log("the pipe is not ready yet, sleeping for 0.01 sec")
            log(f"error: {e}")
            sleep(0.01)
    log(f"test is done, total time was: {time() - start_time} secs")
    sleep(10)


if __name__ == "__main__":
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if len(sys.argv) > 1:
        my_id = int(sys.argv[1])
        num1 = my_id // 200
        num2 = (my_id % 200) + 22
        my_ip = f"10.27.{num1}.{num2}"
        migration_endpoint = (my_ip, MIGRATION_PORT)
        handler = MigrationHandler(listen_endpoint=migration_endpoint)
        handler.start()
        host = "10.27.0.20"
        port = 8088
        mass_test_simple_client(host, port)
    else:
        migration_endpoint = ("10.27.0.2", MIGRATION_PORT)
        handler = MigrationHandler(listen_endpoint=migration_endpoint)
        handler.start()
        host = "10.27.0.20"
        port = 8088
        efficacy_test_wikipedia(host, port, migration=True)
