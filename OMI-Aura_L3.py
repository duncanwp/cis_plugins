from cis.data_io.products import NetCDF_Gridded


class OMI_Aura_L3(NetCDF_Gridded):
    """
        Plugin for reading ECHAM-HAM NetCDF output files.
    """

    @staticmethod
    def load_single_file_callback(cube, field, filename):
        from iris.util import squeeze
        from datetime import datetime
        from iris.coords import AuxCoord
        datetime = datetime(cube.attributes['HDFEOS_ADDITIONAL_FILE_ATTRIBUTES.GranuleYear'],
                            cube.attributes['HDFEOS_ADDITIONAL_FILE_ATTRIBUTES.GranuleMonth'],
                            cube.attributes['HDFEOS_ADDITIONAL_FILE_ATTRIBUTES.GranuleDay'],
                            12, 0, 0)
        cube.add_aux_coord(AuxCoord([datetime], standard_name='time'))
        cube.units = 'dobson'
        cube.convert_units()
        # Sometimes it's useful to remove length one dimensions from cubes, squeeze does this for us...
        return squeeze(cube)

    @staticmethod
    def load_multiple_files_callback(cube, field, filename):
        # We need to remove these global attributes when reading multiple files so that the cubes can be properly merged
        # cube.attributes.pop('history', None)
        # cube.attributes.pop('host_name', None)
        # cube.attributes.pop('date_time', None)
        return cube

    def get_variable_names(self, filenames, data_type=None):
        """
        This is exactly the same as the inherited version except I also exclude the mlev dimension
        """
        import iris
        import cf_units as unit
        variables = []

        cubes = iris.load(filenames, callback=self.load_multiple_files_callback)

        for cube in cubes:
            is_time_lat_lon_pressure_altitude_or_has_only_1_point = True
            for dim in cube.dim_coords:
                units = dim.units
                if dim.points.size > 1 and \
                        not units.is_time() and \
                        not units.is_time_reference() and \
                        not units.is_vertical() and \
                        not units.is_convertible(unit.Unit('degrees')) and \
                        dim.var_name != 'mlev':
                    is_time_lat_lon_pressure_altitude_or_has_only_1_point = False
                    break
            if is_time_lat_lon_pressure_altitude_or_has_only_1_point:
                if cube.var_name:
                    variables.append(cube.var_name)
                else:
                    variables.append(cube.name())

        return set(variables)

    def get_file_signature(self):
        return [r'.*\.nc']
