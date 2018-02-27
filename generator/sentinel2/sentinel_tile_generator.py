"""
Sentinel tile generator, implement the tile generator interface for copernicus S2 data
"""

import time
import logging
import os
import tempfile
from datetime import date
from generator.generator_factory import Generator
from utils.tms_helper import bbox_from_xyz
from .utils.sentinel_downloader import read_zones_from_data_file, find_zone, last_image_date_for_zone
from .sentinel_tile_producer import Tile, SENTINE_PRODUCER_INSTANCE


logging.basicConfig(level=logging.DEBUG)
LOGGER = logging.getLogger("wtmse")
ZONES_FEATURES = read_zones_from_data_file()


class SentinelTileGenerator(Generator):
    """
    Sentinel tile generator, implement the tile generator interface for copernicus S2 data
    """
    def __init__(self):
        """
        Init function
        """
        self.__dir_path = os.path.dirname(os.path.realpath(__file__))
        self.__error_file = os.path.join(self.__dir_path, 'data', 'error.jpg')
        self.__fake_file = os.path.join(self.__dir_path, 'data', 'fake.jpg')
        self.__blank_file = os.path.join(self.__dir_path, 'data', 'blank.png')
        self.__last_date_for_today = {}

    def generate_tile(self, tms_x, tms_y, tms_z):
        """
        generate tile implementation, use an sentinel tile producer to treat data
        """
        bbox = bbox_from_xyz(tms_x, tms_y, tms_z)
        zone_top = find_zone(ZONES_FEATURES, bbox[0][0], bbox[0][1])
        zone_bottom = find_zone(ZONES_FEATURES, bbox[1][0], bbox[1][1])
        if zone_bottom is None or zone_top is None:
            return self.__error_file
        LOGGER.debug("Zone top: %s", zone_top.name)
        LOGGER.debug("Zone bottom: %s", zone_bottom.name)

        if zone_top.name == zone_bottom.name:
            zone_name = zone_top.name
            found_date = None
            if date.today() not in self.__last_date_for_today:
                found_date = last_image_date_for_zone(zone_name)
                self.__last_date_for_today[date.today()] = found_date
            else:
                found_date = self.__last_date_for_today[date.today()]

            file_name = zone_name + "_" + str(found_date.year) + "_" + str(found_date.month) + "_" + str(
                found_date.day) + "_" + str(tms_x) + "_" + str(tms_y) + "_" + str(tms_z) + ".png"
            file_path = os.path.join(tempfile.gettempdir(), file_name)

            if os.path.isfile(file_path):
                return file_path
            tile = Tile(zone_name, found_date, bbox, file_path)
            SENTINE_PRODUCER_INSTANCE.produce_request(tile)
            time.sleep(10)
            if os.path.isfile(file_path):
                return file_path
        return self.__blank_file

    def product_type(self,):
        """
        return sentinel2 string
        """
        return "sentinel2"
