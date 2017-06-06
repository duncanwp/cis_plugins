"""
Workaround for a bug introduced in 1.5.2 where all units got converted to lower case....
"""
from cis.data_io.products import AProduct
from cf_units import Unit
import logging


class cis_fast(AProduct):
    # If a file matches the CIS product signature as well as another signature (e.g. because we aggregated from another
    # data product) we need to prioritise the CIS data product
    priority = 100

    def get_file_signature(self):
        return [r'.*\.nc']

    def create_coords(self, filenames, usr_variable=None):
        from cis.data_io.netcdf import read_many_files_individually, get_metadata
        from cis.data_io.Coord import Coord, CoordList
        from cis.data_io.ungridded_data import UngriddedCoordinates, UngriddedData
        from cis.exceptions import InvalidVariableError

        variables = [("longitude", "x"), ("latitude", "y"), ("altitude", "z"), ("time", "t"),
                     ("air_pressure", "p")]

        # if usr_variable is not None:
        #     variables.append((usr_variable, ''))

        logging.info("Listing coordinates: " + str(variables))

        coords = CoordList()
        var_data = read_many_files_individually(filenames, [v[0] for v in variables])
        for var, (name, axis) in zip(var_data.values(), variables):
            try:
                coords.append(Coord(var, get_metadata(var[0]), axis=axis))
            except InvalidVariableError:
                pass

        # Note - We don't need to convert this time coord as it should have been written in our
        #  'standard' time unit

        if usr_variable is None:
            res = UngriddedCoordinates(coords)
        else:
            usr_var_data = read_many_files_individually(filenames, usr_variable)[usr_variable]
            res = UngriddedData(usr_var_data, get_metadata(usr_var_data[0]), coords)

        return res

    def create_data_object(self, filenames, variable):
        return self.create_coords(filenames, variable)

    def get_file_format(self, filename):
        return "NetCDF/CIS"

    def get_file_type_error(self, filename):
        """
        Test that the file is of the correct signature
        :param filename: the file name for the file
        :return: list fo errors or None
        """
        from cis.data_io.netcdf import get_netcdf_file_attributes
        atts = get_netcdf_file_attributes(filename)
        errors = None
        try:
            source = atts['source']
        except KeyError as ex:
            errors = ['No source attribute found in {}'.format(filename)]
        else:
            if not source.startswith('CIS'):
                errors = ['Source ({}) does not match CIS in {}'.format(source, filename)]
        return errors

