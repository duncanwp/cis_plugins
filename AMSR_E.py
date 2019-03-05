from cis.data_io.products.MODIS import MODIS_L3, _get_MODIS_SDS_data
import logging


class AMSR_E_L3(MODIS_L3):

    def get_file_signature(self):
        product_names = ['AMSR_E_L3_DailyOcean']
        regex_list = [r'.*' + product + '.*\.hdf' for product in product_names]
        return regex_list

    def get_variable_names(self, filenames, data_type=None):
        try:
            from pyhdf.SD import SD
        except ImportError:
            raise ImportError("HDF support was not installed, please reinstall with pyhdf to read HDF files.")

        variables = set([])
        for filename in filenames:
            sd = SD(filename)
            for var_name, var_info in sd.datasets().items():
                # Check that the dimensions are correct
                if var_info[0] == ('YDim:GlobalGrid', 'XDim:GlobalGrid'):
                    variables.add(var_name)

        return variables

    def _create_cube(self, filenames, variable):
        import numpy as np
        from cis.data_io.hdf import _read_hdf4
        from cis.data_io import hdf_vd
        from iris.cube import Cube, CubeList
        from iris.coords import DimCoord, AuxCoord
        from cis.time_util import calculate_mid_time, cis_standard_time_unit
        from cis.data_io.hdf_sd import get_metadata
        from cf_units import Unit

        variables = ['XDim:GlobalGrid', 'YDim:GlobalGrid', variable]
        logging.info("Listing coordinates: " + str(variables))

        cube_list = CubeList()
        # Read each file individually, let Iris do the merging at the end.
        for f in filenames:
            sdata, vdata = _read_hdf4(f, variables)

            lat_points = np.linspace(-90., 90., hdf_vd.get_data(vdata['YDim:GlobalGrid']))
            lon_points = np.linspace(-180., 180., hdf_vd.get_data(vdata['XDim:GlobalGrid']))

            lat_coord = DimCoord(lat_points, standard_name='latitude', units='degrees')
            lon_coord = DimCoord(lon_points, standard_name='longitude', units='degrees')

            # create time coordinate using the midpoint of the time delta between the start date and the end date
            start_datetime = self._get_start_date(f)
            end_datetime = self._get_end_date(f)
            mid_datetime = calculate_mid_time(start_datetime, end_datetime)
            logging.debug("Using {} as datetime for file {}".format(mid_datetime, f))
            time_coord = AuxCoord(mid_datetime, standard_name='time', units=cis_standard_time_unit,
                                  bounds=[start_datetime, end_datetime])

            var = sdata[variable]
            metadata = get_metadata(var)

            try:
                units = Unit(metadata.units)
            except ValueError:
                logging.warning("Unable to parse units '{}' in {} for {}.".format(metadata.units, f, variable))
                units = None

            cube = Cube(_get_MODIS_SDS_data(sdata[variable]),
                        dim_coords_and_dims=[(lon_coord, 1), (lat_coord, 0)],
                        aux_coords_and_dims=[(time_coord, None)],
                        var_name=metadata._name, long_name=metadata.long_name, units=units)

            cube_list.append(cube)

        # Merge the cube list across the scalar time coordinates before returning a single cube.
        return cube_list.merge_cube()

    def get_file_format(self, filename):
        return "HDF4/AMSR_E_L3"
