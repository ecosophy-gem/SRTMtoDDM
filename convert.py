import gdal 
import numpy as np
import matplotlib.pyplot as plt
from src.utils import Lon2Merc, Lat2Merc, Merc2Lon, Merc2Lat, POLE

import click

def GetHeight(strm15_ds):
    """Get the height
    """
    dem = gdal.DEMProcessing('', strm15_ds, 'hillshade', format='MEM')
    dem_data = dem.ReadAsArray()
    return dem_data

class STRM15toDDMConverter:
    """
    Since STRM15plus is a GeoTIFF, we can use GDAL to convert it to a DDM file.
    We need to iterate over the GeoTIFF and convert each tile to a DDM file.

    First we need to get the tile coordinates for the zoom level we want.
    Then we need to get the GeoTIFF for the tile coordinates.
    Then we need to convert the GeoTIFF to a DDM file.
    """
    def __init__(self, 
                zoom=11, 
                quadSize=33, 
                topleftlon=-180, 
                topleftlat=85, 
                bottomrightlon=180, 
                bottomrightlat=0, 
                strm15file="data/SRTM15+V2.tiff",
                ddmoutputdir="data/SRTM15plus/converted"):

        self.zoom = zoom
        self.quadSize = quadSize
        self.topleftlon = topleftlon
        self.topleftlat = topleftlat
        self.bottomrightlon = bottomrightlon
        self.bottomrightlat = bottomrightlat
        self.ddmoutputdir = ddmoutputdir
        self.strm15file = strm15file
        self.ds = gdal.Open(self.strm15file)
        self.strm15_data = self.ds.ReadAsArray()

    def get_quad_coordinates(self, topleftlon, topleftlat, bottomrightlon, bottomrightlat, quadSize):
        lon_inc = (bottomrightlon - topleftlon) / quadSize
        lat_inc = (topleftlat - bottomrightlat) / quadSize

        lons = []
        lats = []
        for i in range(quadSize):
            lons.append(topleftlon + i * lon_inc)
            lats.append(topleftlat - i * lat_inc)

        return list(zip(lons, lats))

    
    def process(self):

        tile_coordinates = self.get_quad_coordinates(self.topleftlon, self.topleftlat, self.bottomrightlon, self.bottomrightlat, self.quadSize)
        for ele in tile_coordinates:
            ele_top_left_lon = ele[0]
            ele_top_left_lat = ele[1]
            ele_bottom_right_lon = ele_top_left_lon + (self.bottomrightlon - self.topleftlon) / self.quadSize
            ele_bottom_right_lat = ele_top_left_lat - (self.topleftlat - self.bottomrightlat) / self.quadSize

            print(f"Processing {ele_top_left_lon}, {ele_top_left_lat}, {ele_bottom_right_lon}, {ele_bottom_right_lat}")
            
            # Get the tile coordinates
            tile_ds = gdal.Translate('', self.ds, projWin=[ele_top_left_lon, ele_top_left_lat, ele_bottom_right_lon, ele_bottom_right_lat], format='MEM')
            heights = GetHeight(tile_ds)

            # Write the DEM heightmap to a GeoTIFF file as .ddm format
            outputpath = f"{self.ddmoutputdir}/{ele_top_left_lon}/{ele_bottom_right_lon}.ddm"
            gdal.Translate(outputpath, heights, format='GTiff', outputType=gdal.GDT_Int16)

@click.command()
@click.option('--zoom', default=11, help='Zoom level')
@click.option('--quadsize', default=33, help='Quad size')
@click.option('--topleftlon', default=-180, help='Top left longitude')
@click.option('--topleftlat', default=85, help='Top left latitude')
@click.option('--bottomrightlon', default=180, help='Bottom right longitude')
@click.option('--bottomrightlat', default=0, help='Bottom right latitude')
@click.option('--strm15file', default="data/SRTM15+V2.tiff", help='STRM15 file')
@click.option('--ddmoutputdir', default="data/SRTM15plus/converted", help='Output directory')
def main(zoom, quadsize, topleftlon, topleftlat, bottomrightlon, bottomrightlat, strm15file, ddmoutputdir):
    converter = STRM15toDDMConverter(zoom=zoom, quadSize=quadsize, topleftlon=topleftlon, topleftlat=topleftlat, bottomrightlon=bottomrightlon, bottomrightlat=bottomrightlat, strm15file=strm15file, ddmoutputdir=ddmoutputdir)
    converter.process()
    



        


            