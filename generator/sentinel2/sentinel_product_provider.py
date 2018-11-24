import abc

import urllib.request
import urllib.parse
import urllib
import json
import logging
import os.path
import tempfile
import zipfile
import glob
from requests.auth import HTTPBasicAuth
import requests
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

class PEPSSentinelProductDownloader(SentinelProductProvider):

    BASE_URL = 'https://peps.cnes.fr/resto/api/collections/S2ST/search.json'
    def __init__(self):
        USER_ENV_KEY = ('WTMSE'+'_'+self.__class__.__name__+'_USER').upper()
        PASSWORD_ENV_KEY = ('WTMSE'+'_'+self.__class__.__name__+'_PASSWORD').upper()
        

        self.peps_user = os.getenv(USER_ENV_KEY)
        self.peps_password = os.getenv(PASSWORD_ENV_KEY)
        if not self.peps_user :
            LOGGER.error('Set env key : %s', USER_ENV_KEY)
        if not self.peps_password:
            LOGGER.error('Set env key : %s', PASSWORD_ENV_KEY)

    def last_image_date_for_zone(self, zone_name):
        """
        Found last image aviailble for the zone name
        """
        params = {'tileid' : zone_name, 'maxRecords' : 1}

        url_string = PEPSSentinelProductDownloader.BASE_URL + '?' + urllib.parse.urlencode(params)
        try:
            json_result = urllib.request.urlopen(url_string).read()
            results = json.loads(json_result.decode("utf-8"))
            for feature in results.get('features', []):
                datestr = feature['properties']['startDate']
                #2018-11-22T10:53:49.024Z
                dt = datetime.strptime(datestr[:-5], '%Y-%m-%dT%H:%M:%S')
            return dt
        except urllib.error.HTTPError:
            return None

    @abc.abstractmethod
    def product_exist(self, zone_name, date):
        #&startDate=2018-11-20T00:00:00.000Z&completionDate=2018-11-20T23:59:00.000Z
        
        """
        Found last image aviailble for the zone name
        """
        datestr = date.strftime('%Y-%m-%d')
        start_date_end = 'T00:00:00.000Z'
        complet_date_end = 'T23:59:00.000Z'
        params = {'tileid' : zone_name, 'maxRecords' : 1, 'startDate' : datestr+start_date_end, 'completionDate':datestr+complet_date_end}

        url_string = PEPSSentinelProductDownloader.BASE_URL + '?' + urllib.parse.urlencode(params)
        try:
            json_result = urllib.request.urlopen(url_string).read()
            results = json.loads(json_result.decode("utf-8"))
            return len(results.get('features', [])) > 0
        except urllib.error.HTTPError:
            return False

    @abc.abstractmethod
    def find_product_in_zone(self, zone_name, date_product, bands=[2, 3, 4]):
        datestr = date_product.strftime('%Y-%m-%d')
        start_date_end = 'T00:00:00.000Z'
        complet_date_end = 'T23:59:00.000Z'

        params = {'tileid' : zone_name, 'maxRecords' : 1, 'startDate' : datestr+start_date_end, 'completionDate':datestr+complet_date_end}

        url_string = PEPSSentinelProductDownloader.BASE_URL + '?' + urllib.parse.urlencode(params)
        try:
            json_result = urllib.request.urlopen(url_string).read()
            results = json.loads(json_result.decode("utf-8"))
            features = results.get('features', [])
            if len(features) == 1:
                feature = features[0]
                file_name = feature['id']
                folder_path = os.path.join(tempfile.gettempdir(), file_name)
                file_path = os.path.join(tempfile.gettempdir(), file_name+'.zip')
                LOGGER.info("File path will be %s", file_path)
                if os.path.isdir(folder_path):
                    LOGGER.info("Retrieve band downloaded in cache : %s",
                                folder_path)
                else:
                    r = requests.get(feature['properties']['services']['download']['url'], auth=HTTPBasicAuth(self.peps_user, self.peps_password), stream=True)
                    if r.status_code == 200:
                        with open(file_path, 'wb') as f:
                            for chunk in r:
                                f.write(chunk)
                        LOGGER.info("Band downloaded : %s", file_path)
                        zip_ref = zipfile.ZipFile(file_path, 'r')
                        zip_ref.extractall(folder_path)
                        zip_ref.close()
                
                products = {}
                for band in bands:
                    band_name = "B%02d" % band
                    glob_value = glob.glob(os.path.join(folder_path, "S2*","GRANULE","*","IMG_DATA", "*B%02d*" % band))
                    if len(glob_value) == 0:
                        glob_value = glob.glob(os.path.join(folder_path, "S2*","GRANULE","*","IMG_DATA", "*10m", "*B%02d*" % band))
                    if len(glob_value) == 0:
                        LOGGER.error("Impossible to find band B%02d" % band)
                    products[band] = glob_value[0]
                    
                return products
        except urllib.error.HTTPError as err:
            LOGGER.error(err)
            return None



if __name__ == "__main__":
    dl = PEPSSentinelProductDownloader()
    # print(dl.last_image_date_for_zone('31TCJ'))
    # print(dl.product_exist('31TCJ', datetime(2018,11,22)))
    # print(dl.product_exist('31TCJ', datetime(2018,11,20)))
    # print(dl.product_exist('31TCJ', datetime(2018,11,18)))
    print(dl.find_product_in_zone('31TCJ', datetime(2018,11,20)))
    