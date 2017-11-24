"""
CIS plugin which reads the netcdf files in one go rather than once per variable which gets pretty slow

I shouldn't need this once we use Iris to read everything
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
        from cis.data_io.netcdf import read_many_files_individually, get_metadata, get_netcdf_file_variables
        from cis.data_io.Coord import Coord, CoordList
        from cis.data_io.ungridded_data import UngriddedCoordinates, UngriddedData
        from cis.exceptions import InvalidVariableError

        # We have to read it once first to find out which variables are in there. We assume the set of coordinates in
        # all the files are the same
        file_variables = get_netcdf_file_variables(filenames[0])

        axis_lookup = {"longitude": "x", 'latitude': 'y', 'altitude': 'z', 'time': 't', 'air_pressure': 'p'}

        all_coord_variables = [(v, axis_lookup[v]) for v in file_variables if v in axis_lookup]
        # Get rid of any duplicates
        coord_variables = []
        for v in all_coord_variables:
            if v is None or v[1][1] not in [x[1][1] for x in coord_variables]:
                coord_variables.append(v)

        all_variables = coord_variables.copy()
        if usr_variable is not None:
            all_variables.append((usr_variable, ''))

        logging.info("Listing coordinates: " + str(all_variables))

        coords = CoordList()
        var_data = read_many_files_individually(filenames, [v[0] for v in all_variables])
        for name, axis in coord_variables:
            try:
                coords.append(Coord(var_data[name], get_metadata(var_data[name][0]), axis=axis))
            except InvalidVariableError:
                pass

        # Note - We don't need to convert this time coord as it should have been written in our
        #  'standard' time unit

        if usr_variable is None:
            res = UngriddedCoordinates(coords)
        else:
            res = UngriddedData(var_data[usr_variable], get_metadata(var_data[usr_variable][0]), coords)

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

