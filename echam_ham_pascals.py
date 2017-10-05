from cis.data_io.products import NetCDF_Gridded
import cis.data_io.gridded_data as gd
import logging
from cis.utils import demote_warnings


def _get_cubes(filenames, constraints=None, callback=None):
    import iris

    # Removes warnings and prepares for future Iris change
    iris.FUTURE.netcdf_promote = True

    filenames_key = tuple(filenames)
    if filenames_key in gd.CACHED_CUBES:
        all_cubes = gd.CACHED_CUBES[filenames_key]
        # print("Reading cached files: {}".format(filenames_key))
    else:
        with demote_warnings():
            all_cubes = iris.load_raw(filenames, callback=callback)
        gd.CACHED_CUBES[filenames_key] = all_cubes
        # print("Caching files: {}".format(filenames_key))
    if constraints is not None:
        cubes = all_cubes.extract(constraints=constraints)
    else:
        cubes = all_cubes
    return cubes


def load_from_cached_cubes(filenames, constraints=None, callback=None):
    from iris.exceptions import MergeError, ConcatenateError
    cubes = _get_cubes(filenames, constraints, callback)

    try:
        iris_cube = cubes.merge_cube()
    except MergeError as e:
        logging.info("Unable to merge cubes on load: \n {}\nAttempting to concatenate instead.".format(e))
        try:
            iris_cube = cubes.concatenate_cube()
        except ConcatenateError as e:
            logging.error("Unable to concatenate cubes on load: \n {}".format(e))
            raise ValueError("Unable to create a single cube from arguments given: {}".format(constraints))
    except ValueError as e:
        raise ValueError("No cubes found")
    return gd.make_from_cube(iris_cube)


class ECHAM_HAM_Pascals(NetCDF_Gridded):
    """
        Plugin for reading ECHAM-HAM NetCDF output files.
    """

    @staticmethod
    def load_single_file_callback(cube, field, filename):
        from iris.util import squeeze
        # Sometimes it's useful to remove length one dimensions from cubes, squeeze does this for us...
        return squeeze(cube)

    @staticmethod
    def load_multiple_files_callback(cube, field, filename):
        # We need to remove these global attributes when reading multiple files so that the cubes can be properly merged
        cube.attributes.pop('history', None)
        cube.attributes.pop('host_name', None)
        cube.attributes.pop('date_time', None)
        return cube

    def get_variable_names(self, filenames, data_type=None):
        """
        This is exactly the same as the inherited version except I also exclude the mlev dimension
        """
        import iris
        import cf_units as unit
        variables = []

        cubes = _get_cubes(filenames, callback=self.load_multiple_files_callback)

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

    def _add_available_aux_coords(self, cube, filenames):
        from iris.aux_factory import HybridPressureFactory
        from iris.coords import AuxCoord
        from iris.exceptions import CoordinateNotFoundError
        import iris

        try:
            surface_pressure = cube.coord('surface pressure')
        except iris.exceptions.CoordinateNotFoundError as e:
            # If there isn't a surface pressure coordinate we can try and pull out the lowest pressure level
            with demote_warnings():
                surface_pressure_cubes = iris.load(filenames, 'atmospheric pressure at interfaces',
                                                   callback=self.load_multiple_files_callback)
            surface_pressure_cube = surface_pressure_cubes.concatenate_cube()[:, -1, :, :]
            surface_pressure = AuxCoord(points=surface_pressure_cube.data, long_name='surface pressure', units='Pa')
            cube.add_aux_coord(surface_pressure, (0, 2, 3))

        if len(cube.coords(long_name='hybrid level at layer midpoints')) > 0:
            cube.add_aux_factory(HybridPressureFactory(delta=cube.coord('hybrid A coefficient at layer midpoints'),
                                                       sigma=cube.coord('hybrid B coefficient at layer midpoints'),
                                                       surface_air_pressure=surface_pressure))

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
            if source != 'ECHAM6.1':
                    errors = ['Source ({}) does not match ECHAM6.1 in {}'.format(source, filename)]
        return errors


