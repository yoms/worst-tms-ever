#!/usr/bin/python3
"""
wtmse, worst tms ever is a TMS server which handle TMS generator.
TMS generator, generates tiles to serve the data at the client.
"""

import logging
from flask import Flask
from flask import send_file
from flask import request
from flask import abort
from generator.generator_factory import GeneratorFactory
from utils.exception import DataCannotBeComputed, DataNotYetReady, GeneratorNotFound


logging.basicConfig(level=logging.DEBUG)
LOGGER = logging.getLogger("wtmse")
APP = Flask(__name__)

@APP.route('/<string:generator_name>/<int:x_coordinate>/<int:y_coordinate>/<int:z_coordinate>', methods=['GET'])
def get_request_handler(generator_name, x_coordinate, y_coordinate, z_coordinate):
    """
    Handle TMS request and dispatch it between generators.
    """
    LOGGER.debug("Data requested for:")
    LOGGER.debug("X coordinate  : %s", x_coordinate)
    LOGGER.debug("Y coordinate  : %s", y_coordinate)
    LOGGER.debug("Z coordinate  : %s", z_coordinate)
    LOGGER.debug("Generator name: %s", generator_name)
    LOGGER.debug("Request args  : %s", request.args)
    try:
        generator = GeneratorFactory.get_instance().build_generator(generator_name)
    except GeneratorNotFound as err:
        LOGGER.error("Impossible to find generator", generator_name)
        return abort(404)
    try:
        tile = generator.generate_tile(x_coordinate, y_coordinate, z_coordinate, request.args)
        LOGGER.debug("File found, file %s", tile)
        return send_file(tile, mimetype='image/png')
    except DataCannotBeComputed as err:
        tile = generator.get_error_file()
        LOGGER.debug("File cannot be found, return error file %s", tile)
        return abort(404)
    except DataNotYetReady as err:
        tile = generator.get_data_not_yet_ready_file()
        LOGGER.debug("File not yet ready, return error file %s", tile)
        return send_file(tile, mimetype='image/png', cache_timeout=10)
    except Exception as err:
        return abort(404)


if __name__ == '__main__':
    LOGGER.setLevel(logging.DEBUG)
    APP.run(host= '0.0.0.0')
