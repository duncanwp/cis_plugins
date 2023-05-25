from echam_ham_pascals import ECHAM_HAM_Pascals
import cis.data_io.gridded_data as gd
import logging
from cis.utils import demote_warnings


def _get_cubes(filenames, constraints=None, callback=None):
    import iris

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

gd.CACHED_CUBES = {}
gd.load_cube = load_from_cached_cubes


class ECHAM_HAM_63(ECHAM_HAM_Pascals):
    """
        Plugin for reading ECHAM-HAM NetCDF output files. **Air pressure is converted to hPa**
    """
    priority = 100

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
                        dim.var_name != 'lev':
                    is_time_lat_lon_pressure_altitude_or_has_only_1_point = False
                    break
            if is_time_lat_lon_pressure_altitude_or_has_only_1_point:
                if cube.var_name:
                    variables.append(cube.var_name)
                else:
                    variables.append(cube.name())
        return set(variables)

    def _add_available_aux_coords(self, cube, filenames):
        import iris
        from iris.aux_factory import HybridPressureFactory
        from iris.coords import AuxCoord
        from iris.exceptions import CoordinateNotFoundError

        # Only do this for fields with a vertical component - this check is a bit hacky though (doesn't consider 3D with no time...)
        if cube.ndim == 4:
            # Only read the first file for these coefficients as they are time-independant and iris won't merge them
            hybrid_a = _get_cubes(filenames, 'hybrid A coefficient at layer midpoints')
            hybrid_b = _get_cubes(filenames, 'hybrid B coefficient at layer midpoints')

            if not hybrid_a:
                # This might be an afterburned cube, eitherway we can't do anything with it
                return

            hybrid_a_coord = AuxCoord(points=hybrid_a[0].data, 
                    long_name='hybrid A coefficient at layer midpoints', units='Pa', var_name='hyam')
            hybrid_b_coord = AuxCoord(points=hybrid_b[0].data, 
                    long_name='hybrid B coefficient at layer midpoints', units='1', var_name='hybm')

            if cube.coords('surface pressure'):
                surface_pressure = cube.coord('surface pressure')
            elif cube.coords('surface_air_pressure'):
                surface_pressure = cube.coord('surface_air_pressure')
            else:
                try:
                    # If there isn't a surface pressure coordinate we can try loading it manually
                    surface_pressure_cube = _get_cubes(filenames, 'surface_air_pressure',
                                                       callback=self.load_multiple_files_callback).concatenate_cube()
                    surface_pressure = AuxCoord(points=surface_pressure_cube.data,
                                                standard_name='surface_air_pressure', long_name='surface pressure',
                                                units='Pa')
                    cube.add_aux_coord(surface_pressure, (0, 2, 3))
                except ValueError:
                    try:
                        # If there isn't a surface pressure coordinate we can try and pull out the lowest pressure level
                        surface_pressure_cubes = _get_cubes(filenames, 'atmospheric pressure at interfaces',
                                                            callback=self.load_multiple_files_callback)
                        surface_pressure_cube = surface_pressure_cubes.concatenate_cube()[:,-1,:,:]
                        surface_pressure = AuxCoord(points=surface_pressure_cube.data, long_name='surface pressure', units='Pa')
                        cube.add_aux_coord(surface_pressure, (0, 2, 3))
                    except ValueError:
                        # Try and get it from the vphysc stream
                        v_files = ['_'.join(f.split('_')[:-1]) + '_vphyscm.nc' for f in filenames]
                        try:
                            surface_pressure_cubes = _get_cubes(v_files, 'atmospheric pressure at interfaces',
                                                                callback=self.load_multiple_files_callback)
                        except:
                            # If we can't do that then just exit - there must be a cleaner way to do this...
                            return
                        surface_pressure_cube = surface_pressure_cubes.concatenate_cube()[:,-1,:,:]
                        surface_pressure = AuxCoord(points=surface_pressure_cube.data, long_name='surface pressure', units='Pa')
                        cube.add_aux_coord(surface_pressure, (0, 2, 3))

            # First convert the hybrid coefficients to hPa, so that air pressure will be in hPa
            hybrid_a_coord.convert_units('hPa')
            surface_pressure.convert_units('hPa')

            cube.add_aux_coord(hybrid_a_coord, (1,))
            cube.add_aux_coord(hybrid_b_coord, (1,))

            if len(cube.coords(long_name='hybrid level at layer midpoints')) > 0:
                cube.add_aux_factory(HybridPressureFactory(delta=hybrid_a_coord, sigma=hybrid_b_coord,
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
            if source != 'ECHAM6.3':
                    errors = ['Source ({}) does not match ECHAM6.1 in {}'.format(source, filename)]
        return errors

