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

gd.CACHED_CUBES = {}
gd.load_cube = load_from_cached_cubes


class MRI_ESM(NetCDF_Gridded):
    """
        Plugin for reading ECHAM-HAM NetCDF output files. **Air pressure is converted to hPa**
    """
    priority = 100

    def _add_available_aux_coords(self, cube, filenames):
        from iris.aux_factory import HybridPressureFactory
        from iris.coords import AuxCoord
        from cis.data_io.netcdf import read

        ps_filenames = [f.replace('concbc', 'ps_TL95L80_192x48NH_3hr') for f in filenames]

        # These will be the same for all files
        hybrid_a = read(ps_filenames[0], 'a')['a']
        hybrid_b = read(ps_filenames[0], 'b')['b']

        hybrid_a_coord = AuxCoord(points=hybrid_a[:], long_name='vertical coordinate formula term: a(k)', units='Pa')
        hybrid_b_coord = AuxCoord(points=hybrid_b[:], long_name='vertical coordinate formula term: b(k)', units='1')

        # This needs to be from each file and then merged
        surface_pressure_cube = _get_cubes(ps_filenames, 'ps',
                                           callback=self.load_multiple_files_callback).concatenate_cube()
        surface_pressure = AuxCoord(points=surface_pressure_cube.data,
                                    standard_name='surface_air_pressure', long_name='surface pressure',
                                    units='Pa')
         # First convert the hybrid coefficients to hPa, so that air pressure will be in hPa
        hybrid_a_coord.convert_units('hPa')
        surface_pressure.convert_units('hPa')

        cube.add_aux_coord(surface_pressure, (0, 2, 3))

        cube.add_aux_coord(hybrid_a_coord, (1,))
        cube.add_aux_coord(hybrid_b_coord, (1,))

        cube.add_aux_factory(HybridPressureFactory(delta=hybrid_a_coord, sigma=hybrid_b_coord,
                                                   surface_air_pressure=surface_pressure))
