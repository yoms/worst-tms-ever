"""
Sentinel tile producer module
"""
import os
import tempfile
from threading import Thread
from queue import Queue
from .utils.sentinel_downloader import download_product_in_zone
from .utils.tile_generator import get_x_y_for_lon_lat, create_raster_from_band, extract_tile, create_png_from_raster


class Tile:
    """
    Tile class, represent a tile request
    """
    def __init__(self, zone_name, found_date, bbox, file_path, bands, first_clip, second_clip, third_clip):
        self.zone_name = zone_name
        self.found_date = found_date
        self.bbox = bbox
        self.file_path = file_path
        self.bands = bands
        self.first_clip = first_clip
        self.second_clip = second_clip
        self.third_clip = third_clip


class SentinelTileProducer(Thread):
    """
    Ascync sentinel tile producer, produce tile from a request queue
    """

    tile_to_product = Queue()

    def __init__(self):
        """
        init
        """
        Thread.__init__(self)

    @staticmethod
    def produce_request(tile):
        """
        Add a tile request in the queue
        """
        SentinelTileProducer.tile_to_product.put(tile)

    def run(self):
        """
        Get tiles requests from the queue and treat it
        """
        while True:
            tile = SentinelTileProducer.tile_to_product.get()
            zone_name = tile.zone_name
            found_date = tile.found_date
            bbox = tile.bbox
            file_path = tile.file_path
            tile_bands = tile.bands
            first_clip = tile.first_clip
            second_clip = tile.second_clip
            third_clip = tile.third_clip

            if not os.path.isfile(file_path):
                bands = download_product_in_zone(zone_name, found_date, tile_bands)
                tiff_name = zone_name + "_" + \
                    str(found_date.year) + "_" + \
                    str(found_date.month) + "_" + str(found_date.day) + \
                    "_"+str(tile_bands[0])+"_"+str(tile_bands[1])+"_"+str(tile_bands[2])
                tiff_path = os.path.join(tempfile.gettempdir(), tiff_name)

                if not os.path.isfile(tiff_path):
                    create_raster_from_band(
                        bands[tile_bands[0]], bands[tile_bands[1]], bands[tile_bands[2]], tiff_path)

                big_png_name = zone_name + "_" + \
                    str(found_date.year) + "_" + str(found_date.month) + \
                    "_" + str(found_date.day) + \
                    "_"+str(tile_bands[0])+"_"+str(tile_bands[1])+"_"+str(tile_bands[2])+ \
                    "_"+str(first_clip[0])+"_"+str(first_clip[1])+ \
                    "_"+str(second_clip[0])+"_"+str(second_clip[1])+ \
                    "_"+str(third_clip[0])+"_"+str(third_clip[1])+ \
                    ".png"
                big_png_path = os.path.join(
                    tempfile.gettempdir(), big_png_name)
                if not os.path.isfile(big_png_path):
                    create_png_from_raster(tiff_path, big_png_path, first_clip, second_clip, third_clip)

                top_left = get_x_y_for_lon_lat(
                    tiff_path, bbox[0][0], bbox[0][1])
                top_rigth = get_x_y_for_lon_lat(
                    tiff_path, bbox[0][0], bbox[1][1])
                bottom_left = get_x_y_for_lon_lat(
                    tiff_path, bbox[1][0], bbox[0][1])
                bottom_right = get_x_y_for_lon_lat(
                    tiff_path, bbox[1][0], bbox[1][1])
                extract_tile(big_png_path, top_left, top_rigth,
                             bottom_left, bottom_right, file_path)


SENTINE_PRODUCER_INSTANCE = SentinelTileProducer()
SENTINE_PRODUCER_INSTANCE.start()
