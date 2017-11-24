"""
A plugin for reading converted ICARTT files
"""
from cis.data_io.products import AProduct
import logging


class icartt_netcdf(AProduct):

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

        def get_axis_std_name(var):
            axis=None
            lvar = var.lower()
            if lvar == 'longitude':
                axis = 'x', 'longitude'
            if lvar == 'latitude':
                axis = 'y', 'latitude'
            if lvar == 'G_ALT' or lvar == 'altitude':
                axis = 'z', 'altitude'
            if lvar == 'time':
                axis = 't', 'time'
            if lvar == 'p' or lvar == 'pressure':
                axis = 'p', 'air_pressure'
            return axis

        all_coord_variables = [(v, get_axis_std_name(v)) for v in file_variables if get_axis_std_name(v) is not None]
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
        for name, axis_std_name in coord_variables:
            try:
                meta = get_metadata(var_data[name][0])
                if meta.standard_name is None:
                    meta.standard_name = axis_std_name[1]
                coords.append(Coord(var_data[name], meta, axis=axis_std_name[0]))
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
        return "NetCDF/ICARTT"

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
            history = atts['history']
        except KeyError as ex:
            errors = ['No history attribute found in {}'.format(filename)]
        else:
            if "Assembled using assemble and _readict" not in history:
                errors = ['History ({}) does not appear to match ICARTT output in {}'.format(history, filename)]
        return errors

