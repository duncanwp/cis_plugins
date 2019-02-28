__author__ = 'watson-parris'
from cis.data_io.products.HadGEM import HadGEM_PP
import logging


class HadGEM_unknown_vars(HadGEM_PP):

    def get_variable_names(self, filenames, data_type=None):
        import iris
        import cf_units as unit
        from cis.utils import single_warnings_only
        # Removes warnings and prepares for future Iris change
        iris.FUTURE.netcdf_promote = True

        variables = []

        # Filter the warnings so that they only appear once - otherwise you get lots of repeated warnings
        with single_warnings_only():
            cubes = iris.load(filenames)

        for cube in cubes:
            is_time_lat_lon_pressure_altitude_or_has_only_1_point = True
            for dim in cube.dim_coords:
                units = dim.units
                if dim.points.size > 1 and \
                        not units.is_time() and \
                        not units.is_time_reference() and \
                        not units.is_vertical() and \
                        not units.is_convertible(unit.Unit('degrees')):
                    is_time_lat_lon_pressure_altitude_or_has_only_1_point = False
                    break
            if is_time_lat_lon_pressure_altitude_or_has_only_1_point:
                name = cube.var_name or cube.name()
                if name == 'unknown' and 'STASH' in cube.attributes:
                    name = '{}'.format(cube.attributes['STASH'])
                variables.append(name)

        return set(variables)

    @staticmethod
    def load_multiple_files_callback(cube, field, filename):
        # This method sets the var_name (used for outputting the cube to NetCDF) to the cube name. This can be quite
        #  for some HadGEM variables but most commands allow the user to override this field on output.
        var_name = cube.name()
        if var_name == 'unknown' and 'STASH' in cube.attributes:
            var_name = '{}'.format(cube.attributes['STASH'])
        try:
            cube.var_name = var_name
        except ValueError as e:
            logging.info("Unable to set var_name due to error: {}".format(e))

    @staticmethod
    def load_single_file_callback(cube, field, filename):
        # This method sets the var_name (used for outputting the cube to NetCDF) to the cube name. This can be quite
        #  for some HadGEM variables but most commands allow the user to override this field on output.
        var_name = cube.name()
        if var_name == 'unknown' and 'STASH' in cube.attributes:
            var_name = '{}'.format(cube.attributes['STASH'])
        try:
            cube.var_name = var_name
        except ValueError as e:
            logging.info("Unable to set var_name due to error: {}".format(e))
