"""
Sentinel tile generator, implement the tile generator interface for copernicus S2 data
"""

import time
import logging
import os
import tempfile
import datetime
from datetime import date
from generator.generator_factory import Generator
from utils.tms_helper import bbox_from_xyz
from utils.exception import DataCannotBeComputed, DataNotYetReady
from .utils.sentinel_downloader import read_zones_from_data_file, find_zone
from .sentinel_tile_producer import Tile, SentinelImageProducer
from .sentinel_product_provider import SentinelProductProvider, SentinelProductDownloader


logging.basicConfig(level=logging.DEBUG)
LOGGER = logging.getLogger("wtmse")
ZONES_FEATURES = read_zones_from_data_file()
MAXIMUM_SLEEP = 60

class SentinelTileGenerator(Generator):
    """
    Sentinel tile generator, implement the tile generator interface for copernicus S2 data
    """
    __last_date_for_today = {}
    ProductProviderClass = None

    def __init__(self):
        """
        Init function
        """
        self.__dir_path = os.path.dirname(os.path.realpath(__file__))
        self.__error_file = os.path.join(self.__dir_path, 'data', 'error.jpg')
        self.__fake_file = os.path.join(self.__dir_path, 'data', 'fake.jpg')
        self.__blank_file = os.path.join(self.__dir_path, 'data', 'blank.png')
        self.product_provider = SentinelTileGenerator.ProductProviderClass()
        SentinelImageProducer.ProductProviderClass = SentinelTileGenerator.ProductProviderClass

    def get_data_not_yet_ready_file(self):
        LOGGER.debug("Data not yet ready, send %s", self.__blank_file)
        return self.__blank_file

    def get_error_file(self):
        LOGGER.debug("Error in request, send %s", self.__error_file)
        return self.__error_file


    def generate_file_name(self, zone_name, date, tms_x, tms_y, tms_z, bands, first_clip, second_clip, third_clip):
        file_name = zone_name + "_" + \
        str(date.year) + "_" + str(date.month) +  "_" + str(date.day) + \
        "_" + str(tms_x) + "_" + str(tms_y) + "_" + str(tms_z) + \
        "_"+str(bands[0])+"_"+str(bands[1])+"_"+str(bands[2])+ \
        "_"+str(first_clip[0])+"_" +str(first_clip[1])+ \
        "_"+str(second_clip[0])+"_"+str(second_clip[1])+ \
        "_"+str(third_clip[0])+"_" +str(third_clip[1])+ \
        ".png"
        return file_name
    
    def parse_arguments(self, arguments):
        """
        Parse argument function
        """
        bands = [2, 3, 4]
        first_clip = (0., 2500.)
        second_clip = first_clip
        third_clip = first_clip
        zone_name = None
        date_requested = None

        if 'bands' in arguments:
            bands = list(map(int,arguments.get('bands', '2,3,4').split(',')))

        def parse_clip(arg_string):        
            if arg_string in arguments:
                return tuple(map(float,arguments.get(arg_string, '0,2500').split(',')))
            return (0., 2500.)
        
        first_clip = parse_clip('first_clip')
        second_clip = parse_clip('second_clip')
        third_clip = parse_clip('third_clip')

        if "zone" in arguments:
            zone_name=arguments.get("zone")
        
        if "date" in arguments:
            date_requested = arguments.get("date")
            date_requested = datetime.datetime.strptime(date_requested, '%Y%m%d').date()

        return bands, first_clip, second_clip, third_clip, zone_name, date_requested
        
    def generate_tile(self, tms_x, tms_y, tms_z, arguments):
        """
        generate tile implementation, use an sentinel tile producer to treat data
        """

        if (tms_z < 9) or (tms_z > 14):
            LOGGER.debug("Image shall be between 9 < z < 14 ")
            raise DataCannotBeComputed("Image shall be between 9 < z < 14 ")
        bbox = bbox_from_xyz(tms_x, tms_y, tms_z)
        zone_top = find_zone(ZONES_FEATURES, bbox[0][0], bbox[0][1])
        zone_bottom = find_zone(ZONES_FEATURES, bbox[1][0], bbox[1][1])
        if zone_bottom is None or zone_top is None:
            raise DataCannotBeComputed("Impossible to find zone ")
        LOGGER.debug("Zone top: %s", zone_top.name)
        LOGGER.debug("Zone bottom: %s", zone_bottom.name)

        if zone_top.name == zone_bottom.name:
            found_date = None

            bands, first_clip, second_clip, third_clip, zone_name, found_date = self.parse_arguments(arguments)

            if zone_name is not None and zone_name != zone_bottom.name:
                raise DataCannotBeComputed("Data not requested")
            zone_name = zone_top.name
            if found_date is None:
                if zone_top.name not in SentinelTileGenerator.__last_date_for_today:
                        found_date = self.product_provider.last_image_date_for_zone(zone_name)
                        SentinelTileGenerator.__last_date_for_today[zone_top.name] = (date.today(),found_date)
                else:
                    if SentinelTileGenerator.__last_date_for_today[zone_top.name][0] != date.today():
                        found_date = self.product_provider.last_image_date_for_zone(zone_name)
                        SentinelTileGenerator.__last_date_for_today[zone_top.name] = (date.today(),found_date)
                    else:
                        found_date = SentinelTileGenerator.__last_date_for_today[zone_top.name][1]
                if found_date is None:
                    raise DataCannotBeComputed("Impossible to find date for zone")

            file_name = self.generate_file_name(zone_name ,found_date,tms_x,tms_y,tms_z,bands, first_clip, second_clip, third_clip)
            file_path = os.path.join(tempfile.gettempdir(), file_name)

            if os.path.isfile(file_path):
                return file_path

            tile = Tile(zone_name, found_date, bbox, file_path, bands, first_clip, second_clip, third_clip)
            SentinelImageProducer.produce_request(tile)

            actual_sleep = 0
            while not os.path.exists(file_path) and actual_sleep < MAXIMUM_SLEEP:
                time.sleep(1)
                actual_sleep = actual_sleep + 1

            if os.path.isfile(file_path):
                return file_path
            LOGGER.debug("Data not yet ready")
            raise DataNotYetReady("File not yet ready, retry later")
        else:
            raise DataCannotBeComputed("Image shall be in the same tile")


    def product_type(self,):
        """
        return sentinel2 string
        """
        return "sentinel2"
