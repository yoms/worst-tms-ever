import abc

import urllib.request
import logging
import os.path
import tempfile
from datetime import datetime, timedelta, date

logging.basicConfig(level=logging.DEBUG)
LOGGER = logging.getLogger("sentinel-product-provider")





class SentinelProductProvider:

    def last_image_date_for_zone(self, zone_name):
        """
        Found last image aviailble for the zone name
        """
        date_buffer = date.today()
        while self.product_exist(zone_name, date_buffer) != True:
            date_buffer = date_buffer - timedelta(days=1)
            LOGGER.debug("Try date time : %s", date_buffer)
        return date_buffer

    @abc.abstractmethod
    def product_exist(self, zone_name, date):
        raise NotImplementedError()

    @abc.abstractmethod
    def find_product_in_zone(self, zone_name, date_product, bands=[2, 3, 4]):
        raise NotImplementedError()



class SentinelProductDownloader(SentinelProductProvider):
    BASE_URL = 'https://sentinel-s2-l1c.s3.amazonaws.com/tiles'


    def get_url_for_zone(self, zone_name):
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
        return SentinelProductDownloader.BASE_URL + "/" + utm_code + "/" + lat_band + "/" + square

    @abc.abstractmethod
    def product_exist(self, zone_name, date_product):
        """
        Verify if product exist in the given zone for the given date
        """
        zone_url = self.get_url_for_zone(zone_name)
        url_string = zone_url + "/" + \
            str(date_product.year) + "/" + str(date_product.month) + \
            "/" + str(date_product.day) + "/0/preview.jpg"
        LOGGER.debug("Request url : %s ", url_string)
        try:
            urllib.request.urlopen(url_string).read()
            return True
        except urllib.error.HTTPError:
            return False

    @abc.abstractmethod
    def find_product_in_zone(self, zone_name, date_product, bands=[2, 3, 4]):
        """
        Download product for the given date and the given zone
        """
        zone_url = self.get_url_for_zone(zone_name)

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