# Worst TMS EVER

This python flask server, serv TMS data from copernicus raster, its the worst TMS cause the computing time long and requests going in time out.

For now the server take the last image found and create a tile from it.


## Caution

Unzip ./generator/sentinel2/utils/data/S2A_OPER.kml.zip before use

## Once launch

Server will be launch on port 5000

You can access to data with url like this:

http://localhost:5000/4108/3017/13

http://localhost:5000/{x}/{y}/{z}

The request can take a long time, if the data was not already computed the wtmse will download the data and process the tile.

# TODO

- [ ] Defnie the generator requested in the request
- [ ] Pass argument to improve the wtmse (date of image, color clip, band used)