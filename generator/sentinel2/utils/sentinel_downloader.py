"""
Utils function to download sentinel S2 images
"""
import urllib.request
import logging
import os.path
import tempfile
from datetime import datetime, timedelta, date
import shapely.wkt
import numpy as np
from fastkml import kml
from shapely.geometry import Point, Polygon

logging.basicConfig(level=logging.DEBUG)
LOGGER = logging.getLogger("sentinel-downloader")
DIR_PATH = os.path.dirname(os.path.realpath(__file__))
GRANULE_KML_FILE = os.path.join(DIR_PATH, 'data', 'S2A_OPER.kml')
BASE_URL = 'https://sentinel-s2-l1c.s3.amazonaws.com/tiles'


def read_zones_from_data_file():
    """
    Read zone file
    """
    LOGGER.debug("Read zones from kml data %s", GRANULE_KML_FILE)
    with open(GRANULE_KML_FILE, 'rb') as kmlfile:
        doc = kmlfile.read()

    k = kml.KML()
    k.from_string(doc)

    file_feature = list(k.features())[0]
    features = list(file_feature.features())
    zones_features = list(features[0].features())
    zones_dict = {}
    for zone in zones_features:
        top_x = int(zone.geometry.bounds[0])
        top_y = int(zone.geometry.bounds[1])
        if top_x not in zones_dict:
            zones_dict[top_x] = {}
            zones_dict[top_x][top_y] = [zone]
        elif top_y not in zones_dict[top_x]:
            zones_dict[top_x][top_y] = [zone]
        else:
            zones_dict[top_x][top_y].append(zone)
    return zones_dict


def find_zone(zones_features, longitude, latitude):
    """
    Find zone for lat long
    """
    top_x = int(longitude)
    top_y = int(latitude)
    if top_x in zones_features:
        if top_y in zones_features[top_x]:
            zone_x_tab = [zones_features[top_x - 1],
                          zones_features[top_x], zones_features[top_x + 1]]
            for zone_x in zone_x_tab:
                zone_y_tab = [zone_x[top_y - 1],
                              zone_x[top_y], zone_x[top_y + 1]]
                for zone_y in zone_y_tab:
                    for zone in zone_y:
                        zone_geom = shapely.wkt.loads(zone.geometry.to_wkt())
                        if Point(longitude, latitude).within(zone_geom):
                            return zone
    return None


def get_url_for_zone(zone_name):
    """
    Return url for th given zone
    """
    if len(zone_name) < 5:
        LOGGER.debug("Impossible to build url from zone_name %s", zone_name)
        return ""
    utm_code = zone_name[:2]
    lat_band = zone_name[2]
    square = zone_name[-2:]
    if utm_code[0] == '0':
        utm_code = utm_code[1]
    return BASE_URL + "/" + utm_code + "/" + lat_band + "/" + square


def product_exist(zone_name, date_product):
    """
    Verify if product exist in the given zone for the given date
    """
    zone_url = get_url_for_zone(zone_name)
    url_string = zone_url + "/" + \
        str(date_product.year) + "/" + str(date_product.month) + \
        "/" + str(date_product.day) + "/0/preview.jpg"
    LOGGER.debug("Request url : %s ", url_string)
    try:
        urllib.request.urlopen(url_string).read()
        return True
    except urllib.error.HTTPError:
        return False


def download_product_in_zone(zone_name, date_product, bands=[2, 3, 4]):
    """
    Downloaf product for the given date and the given zone
    """
    zone_url = get_url_for_zone(zone_name)

    def download_band(band_name):
        """
        Download a specific band
        """
        url_string = zone_url + "/" + \
            str(date_product.year) + "/" + str(date_product.month) + \
            "/" + str(date_product.day) + "/0/"
        url = url_string + "%s.jp2" % band_name
        try:
            LOGGER.info("Download band %s at %s", band_name, url)
            file_name = zone_name + "_" + \
                str(date_product.year) + "_" + str(date_product.month) + \
                "_" + str(date_product.day) + "_" + str(band_name)
            file_path = os.path.join(tempfile.gettempdir(), file_name)
            LOGGER.info("File path will be %s", file_path)
            if os.path.isfile(file_path):
                LOGGER.info("Retrieve band downloaded in cache : %s",
                            file_path)
            else:
                file_path, headers = urllib.request.urlretrieve(url, file_path)
                LOGGER.info("Band downloaded : %s", file_path)
            return file_path
        except urllib.error.HTTPError:
            LOGGER.info("Impossible to find requested product")
            return None

    products = {}

    for band in bands:
        band_name = "B%02d" % band
        products[band] = download_band(band_name)
    return products


def download_product(longitude, latitude, date_product, bands=[2, 3, 4]):
    """
    Download product at the give lat/long for the given date
    """
    LOGGER.debug("Download product")
    LOGGER.debug("Longitude : %s", longitude)
    LOGGER.debug("Latitude : %s", latitude)
    LOGGER.debug("Date : %s", date_product)
    zones_features = read_zones_from_data_file()
    zone = find_zone(zones_features, longitude, latitude)
    LOGGER.debug("Zone find : %s", zone.name)
    return download_product_in_zone(zone.name, date_product, bands)


def last_image_date_for_lat_lon(latitude, longitude):
    """
    Found last image aviailble for the lat/long
    """
    zones_features = read_zones_from_data_file()
    zone = find_zone(zones_features, latitude, longitude)
    return last_image_date_for_zone(zone.name)


def last_image_date_for_zone(zone_name):
    """
    Found last image aviailble for the zone name
    """
    date_buffer = date.today()
    while product_exist(zone_name, date_buffer) != True:
        date_buffer = date_buffer - timedelta(days=1)
        LOGGER.debug("Try date time : %s", date_buffer)
    return date_buffer
