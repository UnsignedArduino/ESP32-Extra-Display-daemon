import logging
from io import BytesIO
from time import sleep

from PIL import ImageGrab
from serial import Serial

from logger import create_logger

logger = create_logger(name=__name__, level=logging.DEBUG)

SIZE = (320, 240)
BAUD_RATE = 115200
SLEEP_TIME = 0.1


class ESP32ExtraDisplayDaemon:
    """
    The class for the ESP32 Extra Display daemon.
    """

    def __init__(self, path: str):
        """
        Initialize the ESP32 Extra Display daemon.

        :param path: The port to the device. Will not be opened until run().
        """
        logger.debug(f"Assigned port: {path}")
        self.path = path

    def run(self):
        """
        Connects to the device and starts sending frames.
        """
        logger.info(f"Opening port {self.path}")
        with Serial(self.path, BAUD_RATE) as port:
            logger.info(f"Successfully opened port {self.path}")
            while True:
                image = ImageGrab.grab()
                image.thumbnail(SIZE)

                buffer = BytesIO()
                image.save(buffer, "JPEG")

                image_size = buffer.tell()
                buffer.seek(0)

                port.write(f"{image_size}".encode())
                port.write(buffer.read())

                sleep(SLEEP_TIME)
