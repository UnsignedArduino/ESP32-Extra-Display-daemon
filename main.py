import logging
from argparse import ArgumentParser

from serial.tools.list_ports import comports

from logger import create_logger

parser = ArgumentParser(description="Daemon for the ESP32 Extra Display.")
parser.add_argument("-l", "--list-ports", dest="list_ports",
                    action="store_true",
                    help="List serial ports and exit.")
parser.add_argument("-c", "--connect", dest="connect", metavar="PORT",
                    action="store", default=None,
                    help="Connect to an ESP32 Extra Display.")
parser.add_argument("-d", "--debug", dest="debug",
                    action="store_true",
                    help="Whether to show debug output or not.")
args = parser.parse_args()

logger = create_logger(name=__name__, level=logging.INFO)
logger.debug(f"Arguments received: {args}")

if args.debug:
    all_loggers = (
        logger,
    )

    for l in all_loggers:
        l.setLevel(logging.DEBUG)

if args.list_ports:
    logger.info("Listing connected serial ports")
    ports = sorted(comports(), key=lambda p: p.name)
    for index, port in enumerate(ports):
        port_index = f"{index + 1}/{len(ports)}:"
        logger.info(f"{port_index} "
                    f"{port.device} - "
                    f"{port.description}")
        indent_space = len(port_index) * " "
        logger.debug(f"{indent_space}HWID: {port.hwid} ")
        for label, value in {
            "VID": port.vid,
            "PID": port.pid,
            "Serial number": port.serial_number,
            "Location": port.location,
            "Manufacturer": port.manufacturer,
            "Product": port.product,
            "Interface": port.interface
        }.items():
            if value is None:
                continue
            logger.debug(f"{indent_space}{label}: {value}")
elif args.connect:
    port_path = args.connect
    if port_path.replace("-", "").isnumeric():
        port_path = int(port_path)
        logger.debug(f"Finding port at index {port_path}")
        ports = sorted(comports(), key=lambda p: p.name)
        if port_path > len(ports) or port_path < 1:
            logger.error(f"No port at index {port_path}! "
                         f"(out of {len(ports)} ports)")
            exit(1)
        port_path = ports[port_path - 1].device
    logger.info(f"Connecting to {port_path}")
else:
    logger.warning("Nothing to do!")
