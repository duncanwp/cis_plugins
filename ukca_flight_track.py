"""
Workaround for a bug introduced in 1.5.2 where all units got converted to lower case....
"""
from cis.data_io.products import AProduct
from cf_units import Unit
import logging


class flight_track(AProduct):

    def get_file_signature(self):
        return [r'.*\.nc']

    def create_coords(self, filenames, usr_variable=None):
        from cis.data_io.netcdf import read_many_files_individually, get_metadata
        from cis.data_io.ungridded_data import UngriddedCoordinates, UngriddedData
        from cis.data_io.Coord import Coord, CoordList
        from cis.exceptions import InvalidVariableError

        variables = [("lon", "x", 'longitude'), ("lat", "y", 'latitude'), ("alt", "z", 'altitude'),
                     ("time", "t", 'time'), ("p", "p", 'air_pressure')]

        logging.info("Listing coordinates: " + str(variables))

        coords = CoordList()
        for variable in variables:
            try:
                var_data = read_many_files_individually(filenames, variable[0])[variable[0]]
                meta = get_metadata(var_data[0])
                meta.standard_name = variable[2]
                # Some of the variables have an illegal name attribute...
                meta.misc.pop('name', None)
                c = Coord(var_data, meta, axis=variable[1])
                if variable[1] == 'z':
                    c.convert_units('m')
                coords.append(c)
            except InvalidVariableError:
                pass

        # Note - We don't need to convert this time coord as it should have been written in our
        #  'standard' time unit

        if usr_variable is None:
            res = UngriddedCoordinates(coords)
        else:
            usr_var_data = read_many_files_individually(filenames, usr_variable)[usr_variable]
            meta =get_metadata(usr_var_data[0])
            # Some of the variables have an illegal name attribute...
            meta.misc.pop('name', None)
            res = UngriddedData(usr_var_data, meta, coords)

        return res

    def create_data_object(self, filenames, variable):
        return self.create_coords(filenames, variable)

    def get_file_format(self, filename):
        return "NetCDF/FlightTrack"

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
            comment = atts['comment']
        except KeyError as ex:
            errors = ['No comment attribute found in {}'.format(filename)]
        else:
            if "Converted by ukca_flight_to_netcdf.py" not in comment:
                errors = ['Comment ({}) does not match ukca_flight in {}'.format(comment, filename)]
        return errors

