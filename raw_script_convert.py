import gdal
import numpy as np
import matplotlib.pyplot as plt
import os
import sys
import math
import click

# This is a raw conversion of C++ code to python from https://github.com/screwt/openglobusddm
# This hasn't been tested and would be converted to a proper python module
# This is just for reference

PI = 3.14159265358979323846
POLE = 20037508.342789244

def Lon2Merc(lon):
	return math.radians(lon) * POLE

def Lat2Merc(lat):
	return math.log(math.tan((90.0 + lat) * PI / 360.0)) / PI * POLE

def Merc2Lon(x):
	return 180.0 * x / POLE

def Merc2Lat(y):
	return 180.0 / PI * (2 * math.atan(math.exp((y / POLE) * PI)) - PI / 2)

def DegTail(deg):
	if deg >= 0:
		return deg - math.floor(deg)
	return (-1)*math.floor(deg) + deg


def LineIntersectPlane(t, l):
	tt20 = [t[2][0] - t[0][0], t[2][1] - t[0][1], t[2][2] - t[0][2]]
	tt10 = [t[1][0] - t[0][0], t[1][1] - t[0][1], t[1][2] - t[0][2]]
	n = [tt20[1] * tt10[2] - tt20[2] * tt10[1], tt20[2] * tt10[0] - tt20[0] * tt10[2], tt20[0] * tt10[1] - tt20[1] * tt10[0]]
	tl00 = [t[0][0] - l[0][0], t[0][1] - l[0][1], t[0][2] - l[0][2]]
	w = [l[1][0] - l[0][0], l[1][1] - l[0][1], l[1][2] - l[0][2]]
	de = (n[0] * tl00[0] + n[1] * tl00[1] + n[2] * tl00[2]) / (n[0] * w[0] + n[1] * w[1] + n[2] * w[2])

	w[0] *= de
	w[1] *= de
	w[2] *= de

	x = [l[0][0] + w[0], l[0][1] + w[1], l[0][2] + w[2]]

	return x[1]


@click.command()
@click.option('--outputdir', '-o', required=True, help='output directory root')
@click.option('--inputdir', '-i', required=True, help='input directory containing hgt files from http://www.viewfinderpanoramas.org/Coverage%20map%20viewfinderpanoramas_org3.htm')
@click.option('--zoomlevel', '-z', default=11, help='target zoom level')
@click.option('--start', '-s', nargs=2, default=[-180, 85], help='Start lon lat coordonates')
@click.option('--end', '-e', nargs=2, default=[180, 0], help='End lon lat coordonates')
@click.option('--quadsize', '-x', default=33, help='Quadsize resolution default 33')
def main(outputdir, inputdir, zoomlevel, start, end, quadsize):

    zoom = zoomlevel
    quadSize = quadsize
    topleftlon = start[0]
    topleftlat = start[1]
    bottomrightlon = end[0]
    bottomrightlat = end[1]

    incLat_merc = []
    incLon_merc = []

    print(f"Zoom: {zoom}\n QuadSize: {quadSize}\n TopLeftLon: {topleftlon}\n TopLeftLat: {topleftlat}\n BottomRightLon: {bottomrightlon}\n BottomRightLat: {bottomrightlat}\n")

    qn_start = Lon2Merc(topleftlon)
    qn_end = Lon2Merc(bottomrightlon)
    qm_start = Lat2Merc(topleftlat)
    qm_end = Lat2Merc(bottomrightlat)


    quadCount = math.pow(2, zoom)
    dstFieldSize = quadCount * (quadSize - 1) + 1
    incLat_merc = incLon_merc = 2.0 * POLE / (dstFieldSize - 1)

    qm_start_in_grid = (POLE - qm_start) / (incLat_merc * (quadSize - 1))
    qm_end_in_grid = (POLE - qm_end) / (incLat_merc * (quadSize - 1))
    qn_start_in_grid = (qn_start - POLE) / (incLon_merc * (quadSize - 1))
    qn_end_in_grid = (qn_end - POLE) / (incLon_merc * (quadSize - 1))

    print(f"qm_start_in_grid: {qm_start_in_grid} <-> {qm_end_in_grid}\n")
    print(f"qn_start_in_grid: {qn_start_in_grid} <-> {qn_end_in_grid}\n")


    hgtFilesGrid = []
    srcHgtFormat = [1201, 1201, 1.0 / 1200.0]
    srcField = [srcHgtFormat[0] * 180 - (180 - 1), srcHgtFormat[1] * 360 - (360 - 1)]
    dstField = [dstFieldSize, dstFieldSize]

    quadSize2 = quadSize * quadSize
    quadHeightData = []

    tr = [[], [], []]
    line = []
    line.append([0.0, 1000000.0, 0.0])
    line.append([0.0, -1000000.0, 0.0])

    lon_d = 0
    lat_d = 0

    coordi = 0
    coordj = 0


    # Python code to convert SRTM data to DDM format

    for qm in range(quadCount):
        if qm > qm_start_in_grid and qm <= qm_end_in_grid:
            print(f"qm = {qm}")
            for qn in range(quadCount):
                isZeroHeight = True
                for i in range(quadSize):
                    for j in range(quadSize):
                        coordi = POLE - ((quadSize - 1) * qm + i) * incLat_merc
                        coordj = (-1) * POLE + ((quadSize - 1) * qn + j) * incLon_merc

                        lat_d = Merc2Lat(coordi)
                        lon_d = Merc2Lon(coordj)

                        if qn == 0 and i == 0 and j == 0 or qn == quadCount - 1 and i == quadSize - 1 and j == quadSize - 1:
                            print(f"lon: {lon_d} lat: {lat_d}")
                        
                        # Get the height of the point
                        demFileIndex_i = int(np.ceil(90.0 - lat_d))
                        demFileIndex_j = int(np.floor(180.0 + lon_d))

                        onedlat = DegTail(lat_d)
                        onedlon = DegTail(lon_d)

                        indLat = int(np.floor(onedlat / srcHgtFormat.cellsize))
                        i00 = 1200 - 1 - indLat
                        j00 = int(np.floor(onedlon / srcHgtFormat.cellsize))

                        # We will use GDAL to get the height from GeoTiff file
                        # h00 = demGrid->GetHeight(demFileIndex_i, demFileIndex_j, i00, j00)
                        # Not tested bit of code

                        h00 = gdal.Open(f"{demFileIndex_i}_{demFileIndex_j}.tif").ReadAsArray(j00, i00, 1, 1)[0][0]
                        h01 = gdal.Open(f"{demFileIndex_i}_{demFileIndex_j}.tif").ReadAsArray(j00 + 1, i00, 1, 1)[0][0]
                        h10 = gdal.Open(f"{demFileIndex_i}_{demFileIndex_j}.tif").ReadAsArray(j00, i00 + 1, 1, 1)[0][0]

                        cornerLat = 90 - demFileIndex_i
                        cornerLon = -180 + demFileIndex_j

                        # Append to the height array to list of list tr 
                        tr[0].append([cornerLon + j00 * srcHgtFormat.cellsize, h00, cornerLat + (indLat + 1) * srcHgtFormat.cellsize])
                        tr[2].append([cornerLon + (j00 + 1) * srcHgtFormat.cellsize, h01, cornerLat + (indLat + 1) * srcHgtFormat.cellsize])
                        tr[1].append([cornerLon + j00 * srcHgtFormat.cellsize, h10, cornerLat + indLat * srcHgtFormat.cellsize])

                        #What is X and Z?? Do we get this from GDAL?

                        X = 0
                        Z = 0

                        line[0][X] = line[1][X] = lon_d
                        line[0][Z] = line[1][Z] = lat_d

                        h11 = 0

                        edge = ((line[0][X] - tr[2][X]) * (tr[1][Z] - tr[2][Z]) - (line[0][Z] - tr[2][Z]) * (tr[1][X] - tr[2][X]))

                        if edge < 0.0:
                            h11 = gdal.Open(f"{demFileIndex_i}_{demFileIndex_j}.tif").ReadAsArray(j00 + 1, i00 + 1, 1, 1)[0][0]

                            tr[0] = [cornerLon + (j00 + 1) * srcHgtFormat.cellsize, h11, cornerLat + indLat * srcHgtFormat.cellsize]

                        quadHeightData[i * quadSize + j] = 0

                        if h00 != 0 or h01 != 0 or h10 != 0 or h11 != 0:
                            h = LineIntersectPlane(tr, line)
                            quadHeightData[i * quadSize + j] = h
                            if h > 0:
                                isZeroHeight = False

                if not isZeroHeight:
                    #Create directory if it does not exist

                    zoomDir = f"{outputdir}/{zoom}"
                    if not os.path.exists(zoomDir):
                        os.mkdir(zoomDir)

                    qmDir = f"{zoomDir}/{qm}"
                    if not os.path.exists(qmDir):
                        os.mkdir(qmDir)

                    fileName = f"{qmDir}/{qn}.ddm"

                    print(f"droping: {fileName}")

                    quadHeightData_fl = np.array(quadHeightData, dtype=np.float32)

                    with f"{fileName}" as f:
                        f.write(quadHeightData_fl)