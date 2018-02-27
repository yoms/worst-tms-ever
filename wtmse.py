#!/usr/bin/python3
"""
wtmse, worst tms ever is a TMS server which handle TMS generator.
TMS generator, generates tiles to serve the data at the client.
"""

import logging
from flask import Flask
from flask import send_file
from generator.generator_factory import GeneratorFactory

logging.basicConfig(level=logging.DEBUG)
LOGGER = logging.getLogger("wtmse")
APP = Flask(__name__)

@APP.route('/<int:x_coordinate>/<int:y_coordinate>/<int:z_coordinate>', methods=['GET'])
def get_request_handler(x_coordinate, y_coordinate, z_coordinate):
    """
    Handle TMS request and dispatch it between generators.
    """
    LOGGER.debug("Data requested for:")
    LOGGER.debug("X coordinate: %s", x_coordinate)
    LOGGER.debug("Y coordinate: %s", y_coordinate)
    LOGGER.debug("Z coordinate: %s", z_coordinate)
    generator = GeneratorFactory.get_instance().build_generator("sentinel2")
    tile = generator.generate_tile(x_coordinate, y_coordinate, z_coordinate)
    return send_file(tile, mimetype='image/png')


if __name__ == '__main__':
    LOGGER.setLevel(logging.DEBUG)
    APP.run()
