import math
import os
import struct

import gdal
import numpy as np
import rasterio

POLE = 20037508.34
PI = 3.141592653589793238462


def Merc2Lon(x):
    return 180.0 * x / POLE


def Merc2Lat(y):
    return 180.0 / PI * (2 * math.atan(math.exp((y / POLE) * PI)) - PI / 2)


def Lon2Merc(lon):
    return lon * POLE / 180.0


def Lat2Merc(lat):
    return math.log(math.tan((90.0 + lat) * PI / 360.0)) / PI * POLE


def DegTail(deg):
    if deg >= 0:
        return deg - math.floor(deg)
    return (-1) * math.floor(deg) + deg


def LineIntersectPlane(t, l):
    """
    NOT IMPLEMENTED
    """
    return 0


# def LineIntersectPlane(t, l):
# 	tt20 = [t[2][0] - t[0][0], t[2][1] - t[0][1], t[2][2] - t[0][2]]
# 	tt10 = [t[1][0] - t[0][0], t[1][1] - t[0][1], t[1][2] - t[0][2]]
# 	n = [tt20[1] * tt10[2] - tt20[2] * tt10[1], tt20[2] * tt10[0] - tt20[0] * tt10[2], tt20[0] * tt10[1] - tt20[1] * tt10[0]]
# 	tl00 = [t[0][0] - l[0][0], t[0][1] - l[0][1], t[0][2] - l[0][2]]
# 	w = [l[1][0] - l[0][0], l[1][1] - l[0][1], l[1][2] - l[0][2]]
# 	de = (n[0] * tl00[0] + n[1] * tl00[1] + n[2] * tl00[2]) / (n[0] * w[0] + n[1] * w[1] + n[2] * w[2])

# 	w[0] *= de
# 	w[1] *= de
# 	w[2] *= de

# 	x = [l[0][0] + w[0], l[0][1] + w[1], l[0][2] + w[2]]

# 	return x[1]


class HgtFormat:
    def __init__(self, nrows, ncols, cellsize=0.0):
        self.ncols = ncols
        self.nrows = nrows
        self.cellsize = cellsize

    def Size(self):
        return self.ncols * self.nrows

    def crdtodem(lat, lon, res):
        lt = 0
        ll = 0
        slt = ""
        sll = ""
        res = ""

        if lat >= 0:
            res = "N"
            lt = math.floor(abs(lat))
        else:
            res = "S"
            lt = math.ceil(abs(lat))

        slt = str(lt)

        if len(slt) != 2:
            slt[1] = slt[0]
            slt[0] = "0"
            slt[2] = 0

        res += slt

        if lon >= 0:
            res = "E"
            ll = math.floor(abs(lon))
        else:
            res = "W"
            ll = math.ceil(abs(lon))

        sll = str(ll)

        len = len(sll)
        if len != 3:
            if len == 1:
                sll[2] = sll[0]
                sll[0] = "0"
                sll[1] = "0"
                sll[3] = 0
            elif len == 2:
                sll[2] = sll[1]
                sll[1] = sll[0]
                sll[0] = "0"
                sll[3] = 0

        res += sll

        res += ".hgt"
        return res


class HgtFilesGrid:
    def __init__(self, maxLoadedFiles, filesPath):
        self.maxLoadedFiles = maxLoadedFiles
        self.filesPath = filesPath
        self.files = []
        self.filesCount = 0

    def GetHeight(self, iSquare, jSquare, i, j):
        return [[0, 0], [0, 0]]
