from cis.data_io.products.MODIS import MODIS_L2, _get_MODIS_SDS_data
import logging
from cis.data_io import hdf as hdf
from cis.data_io.Coord import CoordList, Coord
from cis.data_io.ungridded_data import UngriddedData
import numpy as np


def modis5kmto1km(lons5km, lats5km):
    """Getting 1km geolocation for modis from 5km tiepoints.

    http://www.icare.univ-lille1.fr/tutorials/MODIS_geolocation
    """
    from geotiepoints.geointerpolator import \
        GeoInterpolator as SatelliteInterpolator

    # FIXME: I changed the values here to work with MOD06 - but why?!
    cols5km = np.arange(2, 1350, 5) / 5.0
    cols1km = np.arange(1350) / 5.0
    lines = lons5km.shape[0] * 5
    rows5km = np.arange(2, lines, 5) / 5.0
    rows1km = np.arange(lines) / 5.0

    along_track_order = 1
    cross_track_order = 3

    satint = SatelliteInterpolator((lons5km, lats5km),
                                   (rows5km, cols5km),
                                   (rows1km, cols1km),
                                   along_track_order,
                                   cross_track_order,
                                   chunk_size=10)
    satint.fill_borders("y", "x")
    lons1km, lats1km = satint.interpolate()
    return lons1km, lats1km


class MOD06_HACK(MODIS_L2):

    priority = 1

    def __get_data_scale(self, filename, variable):
        from cis.exceptions import InvalidVariableError
        from pyhdf.SD import SD

        try:
            meta = SD(filename).datasets()[variable][0][0]
        except KeyError:
            raise InvalidVariableError("Variable " + variable + " not found")

        for scaling in self.modis_scaling:
            if scaling in meta:
                return scaling
        return None

    def _create_coord_list(self, filenames, variable=None):
        import datetime as dt

        variables = ['Latitude', 'Longitude', 'Scan_Start_Time']
        logging.info("Listing coordinates: " + str(variables))

        sdata, vdata = hdf.read(filenames, variables)

        self.apply_interpolation = False
        if variable is not None:
            scale = self.__get_data_scale(filenames[0], variable)
            self.apply_interpolation = scale == "1km"

        lat = sdata['Latitude']
        lat_data = hdf.read_data(lat, _get_MODIS_SDS_data)
        lon = sdata['Longitude']
        lon_data = hdf.read_data(lon, _get_MODIS_SDS_data)

        if self.apply_interpolation:
            lon_data, lat_data = modis5kmto1km(lon_data[:], lat_data[:])

        lat_metadata = hdf.read_metadata(lat, "SD")
        lat_coord = Coord(lat_data, lat_metadata, 'Y')

        lon_metadata = hdf.read_metadata(lon, "SD")
        lon_coord = Coord(lon_data, lon_metadata, 'X')

        time = sdata['Scan_Start_Time']
        time_metadata = hdf.read_metadata(time, "SD")
        # Ensure the standard name is set
        time_metadata.standard_name = 'time'
        time_data = hdf.read_data(time, _get_MODIS_SDS_data)
        if self.apply_interpolation: 
            time_data = np.repeat(np.repeat(time_data, 5, axis=0), 5, axis=1)
        time_coord = Coord(time_data, time_metadata, "T")
        time_coord.convert_TAI_time_to_std_time(dt.datetime(1993, 1, 1, 0, 0, 0))

        return CoordList([lat_coord, lon_coord, time_coord])

    def create_data_object(self, filenames, variable):
        logging.debug("Creating data object for variable " + variable)

        # reading coordinates
        # the variable here is needed to work out whether to apply interpolation to the lat/lon data or not
        coords = self._create_coord_list(filenames, variable)

        # reading of variables
        sdata, vdata = hdf.read(filenames, variable)

        # retrieve data + its metadata
        var = sdata[variable]
        metadata = hdf.read_metadata(var, "SD")

        # cut off the edges of the data...
        # TODO CHECK THIS IS ACTUALLY VALID BEFORE PUBLISHING ANYTHING WITH THIS
        d = hdf.read_data(var, _get_MODIS_SDS_data)
        if self.apply_interpolation:
            d=d[:, 2:-2]

        return UngriddedData(d, metadata, coords, _get_MODIS_SDS_data)
