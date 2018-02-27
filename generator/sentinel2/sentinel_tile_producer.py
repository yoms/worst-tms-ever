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
    def __init__(self, zone_name, found_date, bbox, file_path):
        self.zone_name = zone_name
        self.found_date = found_date
        self.bbox = bbox
        self.file_path = file_path


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

            if not os.path.isfile(file_path):
                bands = download_product_in_zone(zone_name, found_date)
                tiff_name = zone_name + "_" + \
                    str(found_date.year) + "_" + \
                    str(found_date.month) + "_" + str(found_date.day)
                tiff_path = os.path.join(tempfile.gettempdir(), tiff_name)

                if not os.path.isfile(tiff_path):
                    create_raster_from_band(
                        bands[4], bands[3], bands[2], tiff_path)

                big_png_name = zone_name + "_" + \
                    str(found_date.year) + "_" + str(found_date.month) + \
                    "_" + str(found_date.day) + ".png"
                big_png_path = os.path.join(
                    tempfile.gettempdir(), big_png_name)
                if not os.path.isfile(big_png_path):
                    create_png_from_raster(tiff_path, big_png_path, red_clip=(
                        0, 2500), blue_clip=(0, 2500), green_clip=(0, 2500))

                x_min, y_min = get_x_y_for_lon_lat(
                    tiff_path, bbox[0][0], bbox[0][1])
                x_max, y_max = get_x_y_for_lon_lat(
                    tiff_path, bbox[1][0], bbox[1][1])
                extract_tile(big_png_path, x_min, y_max,
                             x_max, y_min, file_path)


SENTINE_PRODUCER_INSTANCE = SentinelTileProducer()
SENTINE_PRODUCER_INSTANCE.start()
