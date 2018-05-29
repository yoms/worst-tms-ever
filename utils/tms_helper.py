"""
TMS helper provide a function helper to compute bbox from tms_x,tms_y,tms_z data
"""

import math


def bbox_from_xyz(tms_x, tms_y, tms_z):
    """
    bbox_from_xyz, return bbox from tms_x, tms_y, tms_z data
    :param tms_x: tms_x in TMS format
    :param tms_y: tms_y in TMS format
    :param tms_z: tms_z in TMS format
    :return bbox: bbox as a tab
    """
    tile_size = 256
    zoom_zero_resolution = 2 * math.pi * 6378137 / tile_size
    origin = 2 * math.pi * 6378137 / 2.0
    meter_by_pixels = zoom_zero_resolution / (2**tms_z)
    tms_y = (1 << tms_z) - tms_y - 1

    def tile_index_to_meter(index):
        """
        return meter for index
        """
        return meter_by_pixels * (index * tile_size) - origin

    x_min = tile_index_to_meter(tms_x)
    y_min = tile_index_to_meter(tms_y)

    x_max = tile_index_to_meter(tms_x + 1)
    y_max = tile_index_to_meter(tms_y + 1)

    def meter_to_lat_lon(x_meter, y_meter):
        """
        return lat long for metter
        """
        lon = (x_meter / origin) * 180.0
        lat = (y_meter / origin) * 180.0
        lat = 180 / math.pi * \
            (2 * math.atan(math.exp(lat * math.pi / 180.0)) - math.pi / 2.0)
        return [lon, lat]

    bounding_box = [meter_to_lat_lon(
        x_min, y_min), meter_to_lat_lon(x_max, y_max)]
    return bounding_box


if __name__ == '__main__':
    print(bbox_from_xyz(16540.0, 11963.0, 15))  # 1.71410,43.61998
    print(bbox_from_xyz(16540.0, 11964.0, 15))  # 1.71410,43.61998
    print(bbox_from_xyz(16540.0, 11965.0, 15))  # 1.71410,43.61998


    print(bbox_from_xyz(16540.0, 11963.0, 15))  # 1.71410,43.61998
    print(bbox_from_xyz(16541.0, 11963.0, 15))  # 1.71410,43.61998
    print(bbox_from_xyz(16542.0, 11963.0, 15))  # 1.71410,43.61998
