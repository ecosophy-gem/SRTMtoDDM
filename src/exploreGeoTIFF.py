import gdal
import numpy as np
import matplotlib.pyplot as plt
import os
import sys
import math

# Read GeoTIFF SRTM15+ file

def readGeoTiffFile(fileName):
	dataset = gdal.Open(fileName)
	if dataset is None:
		print("Error: Can't open file " + fileName)
		return None

	print("Driver: {}/{}".format(dataset.GetDriver().ShortName, dataset.GetDriver().LongName))
	print("Size is {} x {} x {}".format(dataset.RasterXSize, dataset.RasterYSize, dataset.RasterCount))
	print("Projection is {}".format(dataset.GetProjection()))

	geotransform = dataset.GetGeoTransform()
	if geotransform:
		print("Origin = ({}, {})".format(geotransform[0], geotransform[3]))
		print("Pixel Size = ({}, {})".format(geotransform[1], geotransform[5]))

	band = dataset.GetRasterBand(1)
	print("Band Type={}".format(gdal.GetDataTypeName(band.DataType)))

	min = band.GetMinimum()
	max = band.GetMaximum()
	if not min or not max:
		(min, max) = band.ComputeRasterMinMax(True)
	print("Min={:.3f}, Max={:.3f}".format(min, max))

	if band.GetOverviewCount() > 0:
		print("Band has {} overviews.".format(band.GetOverviewCount()))

	if band.GetRasterColorTable():
		print("Band has a color table with {} entries.".format(band.GetRasterColorTable().GetCount()))

	return dataset

# Plot GeoTIFF file

dataset = readGeoTiffFile("sample.tif")
if dataset is not None:
	band = dataset.GetRasterBand(1)
	data = band.ReadAsArray(0, 0, dataset.RasterXSize, dataset.RasterYSize)
	plt.imshow(data, cmap='gray')
	plt.show()

# Convert GeoTIFF file to DDM Heightmaps using GDAL

def convertGeoTiffToDDM(dataset):
    """
    THIS DOES NOT WORK! output = "zoom/x/y.ddm"
    """
    # Get Heightmap from dataset and convert to DDM

    # Get the height of the point
    lat_d = dataset.GetGeoTransform()[3] # upper left y
    lon_d = dataset.GetGeoTransform()[0] # upper left x

    # Get the number of rows and columns
    rows = dataset.RasterYSize # height
    cols = dataset.RasterXSize # width

    # Get the heightmap
    band = dataset.GetRasterBand(1) 
    data = band.ReadAsArray(0, 0, cols, rows) # We get a 2D array of height values
    
    # Output heightmap as DDM 
    zoom = 15 
    x = int((lon_d + 180) / 360 * 2**zoom)
    y = int((1 - math.log(math.tan(lat_d * math.pi / 180) + 1 / math.cos(lat_d * math.pi / 180)) / math.pi) / 2 * 2**zoom)
    output = str(zoom) + "/" + str(x) + "/" + str(y) + ".ddm"
    print("Output: " + output)

    # Write DDM file

    # Create directory if it doesn't exist
    if not os.path.exists(os.path.dirname(output)):
        try:
            os.makedirs(os.path.dirname(output))
        except OSError as exc:
            if exc.errno != errno.EEXIST:
                raise

    # Write DDM file
    with open(output, 'wb') as f:
        f.write(data)
    
    return output






