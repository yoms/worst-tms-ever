import json
import pytest
from generator.sentinel2.utils.sentinel_downloader import find_zone, read_zones_from_data_file, get_url_for_zone
ZONES_FEATURES = read_zones_from_data_file()

@pytest.mark.parametrize("lat,long,zone_name", [
    (-116.015625,50.51342652633956,None),
    (43.600000,1.433333,  "31TCJ")
]
)
def test_find_zone(lat,long,zone_name):
    if zone_name == None:
        assert find_zone(ZONES_FEATURES, long, lat) == None
    else:
        assert zone_name == find_zone(ZONES_FEATURES, long, lat).name



@pytest.mark.parametrize("zone_name, url", [
    ("31TCJ", "https://sentinel-s2-l1c.s3.amazonaws.com/tiles/31/T/CJ"),
    ("31THR", "https://sentinel-s2-l1c.s3.amazonaws.com/tiles/31/T/HR"),
    ("3J", "")
]
)
def test_url_for_zone(zone_name, url):
    assert get_url_for_zone(zone_name) == url