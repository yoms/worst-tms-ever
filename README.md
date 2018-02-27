# Worst TMS EVER

This python flask server, serv TMS data from copernicus raster, its the worst TMS cause the computing time long and requests going in time out.

## Caution

Unzip ./generator/sentinel2/utils/data/S2A_OPER.kml.zip before use

## Once launch

Server will be launch on port 5000

You can access to data with url like this:

http://localhost:5000/4108/3017/13

http://localhost:5000/{x}/{y}/{z}

The request can take a long time, if the data was not already computed the wtmse will download the data and process the tile.
