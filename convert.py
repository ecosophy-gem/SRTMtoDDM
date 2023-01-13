import math
import os

import click
import matplotlib.pyplot as plt
import numpy as np
import structlog
from osgeo import gdal, osr

logger = structlog.get_logger()


PI = 3.141592653589793238462


def tilex2lon(x: int, z: int) -> float:
    # This is from: https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames
    return float(x) / (1 << z) * 360.0 - 180


def tiley2lat(y: int, z: int) -> float:
    # This is from: https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames
    n = PI - (2.0 * PI * y) / (1 << z)
    return 180.0 / PI * math.atan(0.5 * (math.exp(n) - math.exp(-n)))


def GetHeight(strm15_ds):
    """Get the height"""
    dem = gdal.DEMProcessing("", strm15_ds, "hillshade", format="MEM")
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

    def __init__(
        self,
        zoom=6,
        strm15file="data/SRTM15+V2.tiff",
        ddmoutputdir="data/SRTM15plus/converted",
    ):

        self.zoom = zoom
        self.ddmoutputdir = ddmoutputdir
        self.strm15file = strm15file
        logger.info(
            "STRM15toDDMConverter",
            zoom=zoom,
            strm15file=strm15file,
            ddmoutputdir=ddmoutputdir,
        )
        logger.info("Opening STRM15 GeoTIFF...")
        self.ds = gdal.Open(self.strm15file)
        self.strm15_data = self.ds.ReadAsArray()
        logger.info("STRM15 GeoTIFF opened")

    def get_quad_coordinates(self):
        # we want the bounding box to be a square of size quadSize x quadSize
        # so we need to calculate the increment for the longitude and latitude
        quadcount = 2**self.zoom
        logger.info("Calculating quad coordinates", zoom=self.zoom, quadcount=quadcount)
        tile_coordinates = []
        for x in range(quadcount):
            for y in range(quadcount):
                tile_coordinates.append(
                    [
                        tilex2lon(x, self.zoom),
                        tiley2lat(y, self.zoom),
                        tilex2lon(x + 1, self.zoom),
                        tiley2lat(y + 1, self.zoom),
                    ]
                )
        return tile_coordinates

    def process(self):

        tile_coordinates = self.get_quad_coordinates()
        logger.info("Processing tiles", tilecount=len(tile_coordinates))

        for ele in tile_coordinates:
            ele_top_left_lon = ele[0]
            ele_top_left_lat = ele[1]
            ele_bottom_right_lon = ele[2]
            ele_bottom_right_lat = ele[3]
            logger.info(
                "Processing tile",
                ele_top_left_lon=ele_top_left_lon,
                ele_top_left_lat=ele_top_left_lat,
                ele_bottom_right_lon=ele_bottom_right_lon,
                ele_bottom_right_lat=ele_bottom_right_lat,
            )

            x = int(ele_top_left_lat)
            y = int(ele_top_left_lon)
            tile_name = f"{self.zoom}/{x}/{y}"
            logger.info("Tile name", tile_name=tile_name)

            tile_ds, heights = self.get_height_from_lat_long(
                ele_top_left_lon,
                ele_top_left_lat,
                ele_bottom_right_lon,
                ele_bottom_right_lat,
            )

            # # Plot the tile in geo coordinates
            # plt.imshow(heights, cmap="terrain")
            # plt.show()

            # Save the DDM file
            ddm_file = os.path.join(self.ddmoutputdir, f"ddm/{tile_name}.ddm")
            # create the directory if it doesn't exist
            os.makedirs(os.path.dirname(ddm_file), exist_ok=True)

            logger.info("Saving DDM file", ddm_file=ddm_file)
            with open(ddm_file, "wb") as f:
                f.write(heights.tobytes())

            logger.info("DDM file saved", ddm_file=ddm_file)

            # # Save Numpy array
            # npy_file = os.path.join(self.ddmoutputdir, f"numpy/{tile_name}.npy")
            # # create the directory if it doesn't exist
            # os.makedirs(os.path.dirname(npy_file), exist_ok=True)
            # logger.info("Saving Numpy file", npy_file=npy_file)
            # np.save(npy_file, heights)

            # logger.info("Numpy file saved", npy_file=npy_file)

    def get_height_from_lat_long(
        self,
        ele_top_left_lon,
        ele_top_left_lat,
        ele_bottom_right_lon,
        ele_bottom_right_lat,
    ):
        tile_ds = gdal.Translate(
            "",
            self.ds,
            projWin=[
                ele_top_left_lon,
                ele_top_left_lat,
                ele_bottom_right_lon,
                ele_bottom_right_lat,
            ],
            format="MEM",
        )
        heights = GetHeight(tile_ds)
        return tile_ds, heights


@click.command()
@click.option("--zoom", default=6, help="Zoom level")
@click.option("--strm15file", default="data/SRTM15+V2.tiff", help="STRM15 file")
@click.option(
    "--ddmoutputdir", default="data/SRTM15plus/converted", help="Output directory"
)
def main(
    zoom,
    strm15file,
    ddmoutputdir,
):
    logger.info("Starting conversion")
    converter = STRM15toDDMConverter(
        zoom=zoom,
        strm15file=strm15file,
        ddmoutputdir=ddmoutputdir,
    )
    converter.process()


if __name__ == "__main__":
    main()
