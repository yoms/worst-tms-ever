# Worst TMS EVER

This python flask server, serv TMS data from copernicus raster, its the worst TMS cause the computing time long and requests going in time out.

For now the server take the last image found and create a tile from it.


## Caution

Unzip ./generator/sentinel2/utils/data/S2A_OPER.kml.zip before use

## Once launch

Server will be launch on port 5000

You can access to data with url like this:

http://localhost:5000/sentinel2/4108/3017/13

http://localhost:5000/sentinel2/{x}/{y}/{z}

The request can take a long time, if the data was not already computed the wtmse will download the data and process the tile.

The processing can be configure by the request:

http://localhost:5000/sentinel2/4108/3017/13?first_clip=500,8500&third_clip=500,8500&second_clip=500,8500&bands=2,2,2

# TODO

- [x] Define the generator requested in the request
- [ ] Pass argument to improve the wtmse (date of image, color clip, band used)
- [ ] Handle error properly in generators
- [ ] Write readme for real