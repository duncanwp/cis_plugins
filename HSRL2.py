import logging
from cis.data_io.products import AProduct
from cis.data_io.netcdf import get_data, get_metadata, read_many_files_individually
from iris.coords import DimCoord, AuxCoord
from iris.cube import Cube
from cis.data_io.gridded_data import GriddedData
import cis.utils as utils
from cis.time_util import cis_standard_time_unit
import numpy as np

class hsrl(AProduct):
    def get_file_signature(self):
        return [r'HSRL2.*h5']

    priority = 20

    def get_variable_names(self, filenames, data_type=None):
        from cis.data_io.netcdf import get_netcdf_file_variables, remove_variables_with_non_spatiotemporal_dimensions
        variables = []
        for filename in filenames:
            file_variables = get_netcdf_file_variables(filename)
            remove_variables_with_non_spatiotemporal_dimensions(file_variables, self.valid_dimensions)
            variables.extend(file_variables)
        return set(variables)

    def create_data_object(self, filenames, variable):
        logging.debug("Creating data object for variable " + variable)

        variables = [("ER2_IMU/Longitude", "x"), ("ER2_IMU/Latitude", "y"), ("ER2_IMU/gps_time", "t"),
                     ("State/Pressure", "p"), ("DataProducts/Altitude", "z"),
                     ("header/date", ""), (variable, '')]

        logging.info("Listing coordinates: " + str(variables))

        var_data = read_many_files_individually(filenames, [v[0] for v in variables])

        time_data = utils.concatenate([get_data(i) for i in var_data['ER2_IMU/gps_time']])
        # Date is stored as an array (of length 92??) of floats with format: yyyymmdd
        date_str = str(int(var_data['header/date'][0][0]))
        # Flatten the data by taking the 0th column of the transpose
        time_coord = DimCoord(time_data.T[0], standard_name='time',
                              units='hours since {}-{}-{} 00:00:00'.format(date_str[0:4], date_str[4:6], date_str[6:8]))
        time_coord.convert_units(cis_standard_time_unit)

        alt_data = utils.concatenate([get_data(i) for i in var_data["DataProducts/Altitude"]])
        alt_coord = DimCoord(alt_data[0], standard_name='altitude', units='m')

        pres_data = utils.concatenate([get_data(i) for i in var_data["State/Pressure"]])
        pres_coord = AuxCoord(pres_data, standard_name='air_pressure', units='atm')

        lat_data = utils.concatenate([get_data(i) for i in var_data['ER2_IMU/Latitude']])
        lat_coord = AuxCoord(lat_data.T[0], standard_name='latitude')

        lon_data = utils.concatenate([get_data(i) for i in var_data['ER2_IMU/Longitude']])
        lon_coord = AuxCoord(lon_data.T[0], standard_name='longitude')

        data = utils.concatenate([get_data(i) for i in var_data[variable]])
        metadata = get_metadata(var_data[variable][0])

        cube = Cube(np.ma.masked_invalid(data), long_name=metadata.misc['Description'], units=self.clean_units(metadata.units),
                    dim_coords_and_dims=[(alt_coord, 1), (time_coord, 0)], aux_coords_and_dims=[(lat_coord, (0,)),
                                                                                                (lon_coord, (0,)),
                                                                                                (pres_coord, (0, 1))])
        gd = GriddedData.make_from_cube(cube)
        return gd

    @staticmethod
    def clean_units(units):
        lookup = {'NoUnits': '', 'sr^-1km^-1': 'sr^-1 km^-1', 'per kilometer': 'km-1', 'km^-1': 'km-1'}
        # Get the units from the lookup, if they're not in there use the original
        return lookup.get(units, units)

    def create_coords(self, filenames, variable=None):
        raise NotImplemented()

    def get_file_format(self, filename):
        return "HDF5/HSRL2"

