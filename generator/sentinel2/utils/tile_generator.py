
import os
import logging
import tempfile
import scipy.misc
import numpy as np
from osgeo import gdal, osr, ogr

logging.basicConfig(level=logging.DEBUG)
LOGGER = logging.getLogger("tile-generator")


def create_raster_from_band(red, green, blue, output_file):
    """
    Create a big raster from given bands
    """
    LOGGER.debug("Create big raster in output_file : %s", output_file)
    red_ds = gdal.Open(red)
    nx = red_ds.GetRasterBand(1).XSize
    ny = red_ds.GetRasterBand(1).YSize

    dst_ds = gdal.GetDriverByName('GTiff').Create(
        output_file, ny, nx, 3, gdal.GDT_UInt16)

    dst_ds.SetGeoTransform(red_ds.GetGeoTransform())
    dst_ds.SetProjection(red_ds.GetProjection())

    def write_band(band, index_band):
        LOGGER.debug("Write band : %s", index_band)
        band_ds = gdal.Open(band)
        array = band_ds.GetRasterBand(1).ReadAsArray()
        dst_ds.GetRasterBand(index_band).WriteArray(array)

    write_band(red, 1)
    write_band(blue, 2)
    write_band(green, 3)

    dst_ds.FlushCache()

    dst_ds = None
    LOGGER.debug("Big raster is write in output_file : %s", output_file)


def create_png_from_raster(raster_file, output_file, blue_clip=(0., 2500.), red_clip=(0., 2500.), green_clip=(0., 2500.)):
    """
    Create a big png from the given raster,
    clip data
    """
    LOGGER.debug("Create big png in output_file : %s", output_file)
    raster_ds = gdal.Open(raster_file)
    bytes_max = 255.

    if blue_clip[0] > blue_clip[1]:
        LOGGER.error(
            "Maximum clip value should be higther than the Minimum clip value")
        return False
    if red_clip[0] > red_clip[1]:
        LOGGER.error(
            "Maximum clip value should be higther than the Minimum clip value")
        return False
    if green_clip[0] > green_clip[1]:
        LOGGER.error(
            "Maximum clip value should be higther than the Minimum clip value")
        return False

    def clip_array(band_index, clip):
        """
        Clip array data
        """
        array = np.array(raster_ds.GetRasterBand(band_index).ReadAsArray())
        array = np.clip(array, clip[0], clip[1])
        array = array - clip[0]
        array = (np.float32(array) * bytes_max) / (clip[1] - clip[0])
        array = array.astype(int)
        return array

    LOGGER.debug("Prepare red color, clip raw value at %s, %s", red_clip[0], red_clip[1])
    red_array = clip_array(1, red_clip)
    LOGGER.debug("Prepare green color, clip raw value at %s, %s", green_clip[0], green_clip[1])
    green_array = clip_array(2, green_clip)
    LOGGER.debug("Prepare blue color, clip raw value at %s, %s", blue_clip[0], blue_clip[1])
    blue_array = clip_array(3, blue_clip)

    rgb = np.zeros((len(red_array), len(red_array[0]), 3), dtype=np.uint8)
    rgb[..., 0] = red_array
    rgb[..., 1] = green_array
    rgb[..., 2] = blue_array
    LOGGER.debug("Writing png file in %s", output_file)
    generate_name = tempfile.NamedTemporaryFile().name + ".png"
    scipy.misc.imsave(generate_name, rgb)
    os.rename(generate_name, output_file)
    LOGGER.debug("File writed %s", output_file)
    return True


def get_x_y_for_lon_lat(raster_file, lon, lat):
    """
    Get x, y in the raster for the given lon lat
    """
    LOGGER.debug("Compute x and y from lon lat")
    LOGGER.debug("Longitude : %s", lon)
    LOGGER.debug("Latitude : %s", lat)
    sref = osr.SpatialReference()
    sref.ImportFromEPSG(4326)

    # create a geometry from coordinates
    point = ogr.Geometry(ogr.wkbPoint)
    point.AddPoint(lon, lat)

    raster_ds = gdal.Open(raster_file)
    dref = osr.SpatialReference()
    dref.ImportFromWkt(raster_ds.GetProjection())
    ct = osr.CoordinateTransformation(sref, dref)
    point.Transform(ct)
    point_x = point.GetX()
    point_y = point.GetY()
    LOGGER.debug("Point value in raster proj")
    LOGGER.debug("Point x : %s", point_x)
    LOGGER.debug("Point y : %s", point_y)
    ulx, xres, xskew, uly, yskew, yres = raster_ds.GetGeoTransform()

    LOGGER.debug("Upper left coordinate in proj")
    LOGGER.debug("Point x : %s", ulx)
    LOGGER.debug("Point x : %s", uly)
    lrx = ulx + (raster_ds.RasterXSize * xres)
    lry = uly + (raster_ds.RasterYSize * yres)
    LOGGER.debug("Lower rigth coordinate in proj")
    LOGGER.debug("Point x : %s", lrx)
    LOGGER.debug("Point x : %s", lry)

    LOGGER.debug("Raster resolution")
    LOGGER.debug("Res on X : %s", xres)
    LOGGER.debug("Res on Y : %s", yres)
    point_x = (point_x - ulx) / xres
    point_y = (point_y - uly) / yres

    return (int(point_x), int(point_y))

def extract_tile(img_path, x_min, y_min, x_max, y_max, out_path):
    """
    Extract tile from the image
    """
    LOGGER.debug("Extract tile")
    LOGGER.debug("Extract data from table")
    LOGGER.debug("Min x : %s", x_min)
    LOGGER.debug("Max x : %s", x_max)
    LOGGER.debug("Min y : %s", y_min)
    LOGGER.debug("Max y : %s", y_max)
    img = scipy.misc.imread(img_path)

    y_min = max(0, min(y_min, len(img)))
    y_max = max(0, min(y_max, len(img)))
    x_min = max(0, min(x_min, len(img[0])))
    x_max = max(0, min(x_max, len(img[0])))

    LOGGER.debug("After clamp")
    LOGGER.debug("Min x : %s", x_min)
    LOGGER.debug("Max x : %s", x_max)
    LOGGER.debug("Min y : %s", y_min)
    LOGGER.debug("Max y : %s", y_max)

    LOGGER.debug("Image y: %s", len(img))
    LOGGER.debug("Image x: %s", len(img[0]))

    if y_max == y_min:
        LOGGER.error("After clamp, image size is Null")
        return False
    if x_max == x_min:
        LOGGER.error("After clamp, image size is Null")
        return False
    rgb = np.zeros((y_max - y_min, x_max - x_min, 3), dtype=np.uint8)
    rgb[..., 0] = img[y_min:y_max, x_min:x_max, 0]
    rgb[..., 1] = img[y_min:y_max, x_min:x_max, 1]
    rgb[..., 2] = img[y_min:y_max, x_min:x_max, 2]
    LOGGER.debug("Write tile in output file %s", out_path)
    scipy.misc.imsave(out_path, rgb)
    return True