import logging
from argparse import ArgumentParser
import win32gui

from serial.tools.list_ports import comports

import eedd
from eedd import ESP32ExtraDisplayDaemon
from logger import create_logger

parser = ArgumentParser(description="Daemon for the ESP32 Extra Display.")
parser.add_argument("-lp", "--list-ports", dest="list_ports",
                    action="store_true",
                    help="List serial ports and exit.")
parser.add_argument("-lw", "--list-windows", dest="list_windows",
                    action="store_true",
                    help="List windows and exit. Currently available only on "
                         "Windows.")
parser.add_argument("-c", "--connect", dest="connect", metavar="PORT",
                    action="store", default=None,
                    help="Connect to an ESP32 Extra Display.")
parser.add_argument("-w", "--show-window", dest="show_window",
                    metavar="WINDOW", action="store", default=None,
                    help="Show a window instead of the main screen. "
                         "Currently available only on Windows. "
                         "You can use either the window name, "
                         "(not case sensitive) the window's handle, or the "
                         "window index. (when listing windows with -lw)")
parser.add_argument("-d", "--debug", dest="debug",
                    action="store_true",
                    help="Whether to show debug output or not.")
args = parser.parse_args()

logger = create_logger(name=__name__, level=logging.DEBUG)
logger.debug(f"Arguments received: {args}")

all_loggers = (
    logger,
    eedd.logger
)

for l in all_loggers:
    l.setLevel(logging.DEBUG if args.debug else logging.INFO)

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
elif args.list_windows:
    hwnds = []

    def enum_window_callback(hwnd: int, _):
        hwnds.append(hwnd)

    win32gui.EnumWindows(enum_window_callback, None)

    logger.info(f"Listing {len(hwnds)} window{'s' if len(hwnds) != 1 else ''}")

    for index, window_handle in enumerate(hwnds):
        label = f"{index + 1}/{len(hwnds)} ({window_handle}):"
        title = win32gui.GetWindowText(window_handle)
        if len(title) > 0:
            logger.info(f"{label} {title}")
        else:
            logger.debug(f"{label} {title}")
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
    logger.debug(f"Using port {port_path}")

    window_handle = None

    if args.show_window:
        window_handle = args.show_window
        hwnds = []

        def enum_window_callback(hwnd: int, _):
            hwnds.append(hwnd)

        win32gui.EnumWindows(enum_window_callback, None)

        logger.debug(f"Looking through {len(hwnds)} window handles")

        if isinstance(window_handle, str) or window_handle < len(hwnds):
            for index, hwnd in enumerate(hwnds):
                title = win32gui.GetWindowText(hwnd)
                if window_handle == index:
                    window_handle = hwnd
                    break
                elif str(window_handle).lower() == title.lower():
                    window_handle = hwnd
                    break
            else:
                if isinstance(window_handle, str):
                    logger.error(f"No window with name \"{window_handle}\"!")
                else:
                    logger.error(f"No window at index {window_handle}! "
                                 f"(out of {len(hwnds)} ports)")
                exit(1)
        else:
            if not win32gui.IsWindow(window_handle):
                logger.error(f"{window_handle} does not point to a valid "
                             f"window!")
                exit(1)
    if window_handle:
        logger.debug(f"Using window handle {window_handle} "
                     f"\"{win32gui.GetWindowText(window_handle)}\"")

    eedd = ESP32ExtraDisplayDaemon(port_path, window_handle)
    eedd.run()
else:
    logger.warning("Nothing to do!")
