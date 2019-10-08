"""
Don't drop points with invalid coordinates - there's currently no keyword arg for this
"""
from cis.data_io.products import cis
import logging

class cis_no_postproc(cis):

    def create_data_object(self, filenames, variable):
        data = self.create_coords(filenames, variable)

        # This is pretty hacky but does the job
        data._post_process = lambda: None
        data.update_range()
        return data


class cis_no_altitude(cis):

    def create_coords(self, filenames, usr_variable=None):
        from cis.data_io.netcdf import read_many_files_individually, get_metadata, get_netcdf_file_variables
        from cis.data_io.Coord import Coord, CoordList
        from cis.data_io.ungridded_data import UngriddedCoordinates, UngriddedData
        from cis.exceptions import InvalidVariableError

        # We have to read it once first to find out which variables are in there. We assume the set of coordinates in
        # all the files are the same
        file_variables = get_netcdf_file_variables(filenames[0])

        axis_lookup = {"longitude": "x", 'latitude': 'y', 'time': 't', 'air_pressure': 'p'}

        coord_variables = [(v, axis_lookup[v]) for v in file_variables if v in axis_lookup]

        # Create a copy to contain all the variables to read
        all_variables = list(coord_variables)
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
