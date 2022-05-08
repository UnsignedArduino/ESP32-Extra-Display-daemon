import logging
from ctypes import windll
from io import BytesIO
from time import sleep
from typing import Optional

import win32gui
import win32ui
from PIL import ImageGrab
from PIL import Image
from serial import Serial
from win32gui import error as pywintypes_error

from logger import create_logger

logger = create_logger(name=__name__, level=logging.DEBUG)

SIZE = (320, 240)
BAUD_RATE = 115200
SLEEP_TIME = 0.1


class ESP32ExtraDisplayDaemon:
    """
    The class for the ESP32 Extra Display daemon.
    """

    def __init__(self, path: str, hwnd: Optional[int] = None):
        """
        Initialize the ESP32 Extra Display daemon.

        :param path: The port to the device. Will not be opened until run().
        :param hwnd: A handle to a window to get an image from instead of the
         main screen.
        """
        logger.debug(f"Assigned port: {path}")
        self.path = path
        self.hwnd = hwnd
        if hwnd:
            logger.debug(f"Assigned window: {hwnd}")

    def get_image(self) -> Image.Image:
        """
        Gets an image to show.
        """
        if self.hwnd:
            try:
                left, top, right, bot = win32gui.GetWindowRect(self.hwnd)
                w = right - left
                h = bot - top

                hwndDC = win32gui.GetWindowDC(self.hwnd)
                mfcDC = win32ui.CreateDCFromHandle(hwndDC)
                saveDC = mfcDC.CreateCompatibleDC()

                saveBitMap = win32ui.CreateBitmap()
                saveBitMap.CreateCompatibleBitmap(mfcDC, w, h)

                # https://stackoverflow.com/a/59016194/10291933
                PW_RENDERFULLCONTENT = 0x00000002

                saveDC.SelectObject(saveBitMap)
                result = windll.user32.PrintWindow(self.hwnd,
                                                   saveDC.GetSafeHdc(),
                                                   PW_RENDERFULLCONTENT)

                bmpinfo = saveBitMap.GetInfo()
                bmpstr = saveBitMap.GetBitmapBits(True)

                image = Image.frombuffer("RGB",
                                         (bmpinfo["bmWidth"],
                                          bmpinfo["bmHeight"]),
                                         bmpstr, "raw", "BGRX", 0, 1)

                win32gui.DeleteObject(saveBitMap.GetHandle())
                saveDC.DeleteDC()
                mfcDC.DeleteDC()
                win32gui.ReleaseDC(self.hwnd, hwndDC)
            except pywintypes_error:
                self.hwnd = None
                logger.error(f"Window {self.hwnd} destroyed, resorting to "
                             f"full screen")
                image = ImageGrab.grab()
        else:
            image = ImageGrab.grab()
        image.thumbnail(SIZE)

        sized = Image.new("RGB", SIZE, (0, 0, 0))
        sized.paste(image)

        return sized

    def run(self):
        """
        Connects to the device and starts sending frames.
        """
        logger.info(f"Opening port {self.path}")
        with Serial(self.path, BAUD_RATE) as port:
            logger.info(f"Successfully opened port {self.path}")
            while True:
                image = self.get_image()

                buffer = BytesIO()
                image.save(buffer, "JPEG")

                image_size = buffer.tell()
                buffer.seek(0)

                port.write(f"{image_size}".encode() + buffer.read())

                sleep(SLEEP_TIME)
