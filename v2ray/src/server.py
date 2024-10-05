from proxy import Proxy
from settings import (
    V2RAY_ENDPOINT,
    NAT_ENDPOINT,
    BROKER_ENDPOINT,
    MIGRATION_ENDPOINT,
    POLLING_ENDPOINT,
)
import sys
from logger import log
from types import NoneType


def main(args: list[str]) -> NoneType:
    nat_endpoint = NAT_ENDPOINT
    if len(sys.argv) > 1:
        nat_host, nat_port = sys.argv[1].split(":")
        nat_endpoint = (nat_host, int(nat_port))
        log(f"nat endpoint set to: {nat_host}:{nat_port}", pr=True)

    Proxy(
        V2RAY_ENDPOINT,
        nat_endpoint,
        BROKER_ENDPOINT,
        MIGRATION_ENDPOINT,
        POLLING_ENDPOINT,
    ).run()


if __name__ == "__main__":
    main(sys.argv)
