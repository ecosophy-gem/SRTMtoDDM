import math
import os
import struct
import sys

import click
import gdal
import matplotlib.pyplot as plt
import numpy as np

from src.utils import (
    POLE,
    DegTail,
    HgtFilesGrid,
    HgtFormat,
    Lat2Merc,
    LineIntersectPlane,
    Lon2Merc,
    Merc2Lat,
    Merc2Lon,
)


@click.command()
@click.option("--outputdir", "-o", required=True, help="output directory root")
@click.option(
    "--inputdir",
    "-i",
    required=True,
    help="input directory containing hgt files from http://www.viewfinderpanoramas.org/Coverage%20map%20viewfinderpanoramas_org3.htm",
)
@click.option("--zoomlevel", "-z", default=11, help="target zoom level")
@click.option(
    "--start", "-s", nargs=2, default=[-180, 85], help="Start lon lat coordonates"
)
@click.option("--end", "-e", nargs=2, default=[180, 0], help="End lon lat coordonates")
@click.option("--quadsize", "-x", default=33, help="Quadsize resolution default 33")
def main(outputdir, inputdir, zoomlevel, start, end, quadsize):

    zoom = zoomlevel
    quadSize = quadsize
    topleftlon = start[0]
    topleftlat = start[1]
    bottomrightlon = end[0]
    bottomrightlat = end[1]

    incLat_merc = []
    incLon_merc = []

    print(
        f"Zoom: {zoom}\n QuadSize: {quadSize}\n TopLeftLon: {topleftlon}\n TopLeftLat: {topleftlat}\n BottomRightLon: {bottomrightlon}\n BottomRightLat: {bottomrightlat}\n"
    )

    qn_start = Lon2Merc(topleftlon)
    qn_end = Lon2Merc(bottomrightlon)
    qm_start = Lat2Merc(topleftlat)
    qm_end = Lat2Merc(bottomrightlat)

    print(f"qn_start: {qn_start}")
    print(f"qn_end: {qn_end}")
    print(f"qm_start: {qm_start}")
    print(f"qm_end: {qm_end}")

    quadsCount = pow(2, zoom)
    dstFieldSize = quadsCount * (quadSize - 1) + 1
    incLat_merc = incLon_merc = 2.0 * POLE / (dstFieldSize - 1)

    qm_start_in_grid = (POLE - qm_start) / (incLat_merc * (quadSize - 1))
    qm_end_in_grid = (POLE - qm_end) / (incLat_merc * (quadSize - 1))
    qn_start_in_grid = (qn_start - POLE) / (incLon_merc * (quadSize - 1))
    qn_end_in_grid = (qn_end - POLE) / (incLon_merc * (quadSize - 1))

    print(f"quadsCount: {quadsCount}")
    print(f"dstFieldSize: {dstFieldSize}")
    print(f"incLat_merc: {incLat_merc}")
    print(f"incLon_merc: {incLon_merc}")
    print(f"qm_start_in_grid: {qm_start_in_grid}")
    print(f"qm_end_in_grid: {qm_end_in_grid}")
    print(f"qn_start_in_grid: {qn_start_in_grid}")
    print(f"qn_end_in_grid: {qn_end_in_grid}")

    srcHgtFormat = HgtFormat(1201, 1201, 1.0 / 1200.0)
    srcField = HgtFormat(
        srcHgtFormat.nrows * 180 - (180 - 1), srcHgtFormat.ncols * 360 - (360 - 1)
    )
    dstField = HgtFormat(dstFieldSize, dstFieldSize)

    print(
        f"srcHgtFormat: {srcHgtFormat.ncols} {srcHgtFormat.nrows} {srcHgtFormat.cellsize}"
    )
    print(f"srcField: {srcField.ncols} {srcField.nrows} {srcField.cellsize}")
    print(f"dstField: {dstField.ncols} {dstField.nrows} {dstField.cellsize}")

    quadSize2 = quadSize * quadSize
    quadHeightData = [0] * quadSize2

    tr = [0] * 3
    line = [0] * 2
    line[0] = [0.0, 1000000.0, 0.0]
    line[1] = [0.0, -1000000.0, 0.0]

    lon_d = 0
    lat_d = 0
    coordi = 0
    coordj = 0

    demGrid = HgtFilesGrid(4, inputdir)  # This does not work!!!!

    for qm in range(quadsCount):
        if qm >= qm_start_in_grid and qm <= qm_end_in_grid:
            for qn in range(quadsCount):
                isZeroHeight = True
                for i in range(quadSize):
                    for j in range(quadSize):
                        coordi = POLE - ((quadSize - 1) * qm + i) * incLat_merc
                        coordj = (-1) * POLE + ((quadSize - 1) * qn + j) * incLon_merc

                        lat_d = Merc2Lat(coordi)
                        lon_d = Merc2Lon(coordj)

                        if (qn == 0 and i == 0 and j == 0) or (
                            qn == quadsCount - 1
                            and i == quadSize - 1
                            and j == quadSize - 1
                        ):
                            print(f"lon: {lon_d} lat: {lat_d}")

                        demFileIndex_i = math.ceil(90.0 - lat_d)
                        demFileIndex_j = math.floor(180.0 + lon_d)

                        onedlat = DegTail(lat_d)
                        onedlon = DegTail(lon_d)

                        indLat = math.floor(onedlat / srcHgtFormat.cellsize)
                        i00 = 1200 - 1 - indLat
                        j00 = math.floor(onedlon / srcHgtFormat.cellsize)

                        # Since we don't have a demGrid, we'll just use a dummy value for the height
                        # NOT SURE IF THIS IS CORRECT

                        h00 = demGrid.GetHeight(
                            demFileIndex_i, demFileIndex_j, i00, j00
                        )
                        h01 = demGrid.GetHeight(
                            demFileIndex_i, demFileIndex_j, i00, j00 + 1
                        )
                        h10 = demGrid.GetHeight(
                            demFileIndex_i, demFileIndex_j, i00 + 1, j00
                        )

                        cornerLat = 90 - demFileIndex_i
                        cornerLon = -180 + demFileIndex_j

                        tr[0] = [
                            cornerLon + j00 * srcHgtFormat.cellsize,
                            h00[0],
                            cornerLat + (indLat + 1) * srcHgtFormat.cellsize,
                        ]
                        tr[2] = [
                            cornerLon + (j00 + 1) * srcHgtFormat.cellsize,
                            h01[0] if j00 < srcHgtFormat.ncols - 1 else h00[0],
                            cornerLat + (indLat + 1) * srcHgtFormat.cellsize,
                        ]
                        tr[1] = [
                            cornerLon + j00 * srcHgtFormat.cellsize,
                            h10[0] if i00 < srcHgtFormat.nrows - 1 else h00[0],
                            cornerLat + indLat * srcHgtFormat.cellsize,
                        ]

                        X = 0  # Where is this defined?
                        Z = 2  # Where is this defined?

                        line[0][X] = line[1][X] = lon_d
                        line[0][Z] = line[1][Z] = lat_d

                        h11 = 0

                        edge = (line[0][X] - tr[2][X]) * (tr[1][Z] - tr[2][Z]) - (
                            line[0][Z] - tr[2][Z]
                        ) * (tr[1][X] - tr[2][X])

                        if edge < 0.0:
                            h11 = [0]
                            tr[0] = [
                                cornerLon + (j00 + 1) * srcHgtFormat.cellsize,
                                h11[0]
                                if i00 < srcHgtFormat.nrows - 1
                                and j00 < srcHgtFormat.ncols - 1
                                else h10[0]
                                if i00 < srcHgtFormat.nrows - 1
                                else h01[0]
                                if j00 < srcHgtFormat.nrows - 1
                                else h00[0],
                                cornerLat + indLat * srcHgtFormat.cellsize,
                            ]

                        quadHeightData[i * quadSize + j] = 0

                        if h00[0] != 0 or h01[0] != 0 or h10[0] != 0 or h11[0] != 0:
                            h = LineIntersectPlane(tr, line)  # NOT IMPLEMENTED
                            quadHeightData[i * quadSize + j] = h
                            if h > 0:
                                isZeroHeight = False

                if not isZeroHeight:

                    zoomDir = outputdir + str(zoom)
                    if not os.path.exists(zoomDir):
                        os.mkdir(zoomDir)

                    qmDir = zoomDir + "/" + str(qm)
                    if not os.path.exists(qmDir):
                        os.mkdir(qmDir)

                    fileName = qmDir + "/" + str(qn) + ".ddm"

                    print("droping: " + fileName)

                    with open(fileName, "wb") as fp:
                        quadHeightData_fl = [float(x) for x in quadHeightData]
                        fp.write(struct.pack("<" + "f" * quadSize2, *quadHeightData_fl))
