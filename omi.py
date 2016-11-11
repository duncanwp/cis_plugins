from cis.data_io.products.AProduct import AProduct


class OMI(AProduct):
    """
        Plugin for reading OMI HDF files.
    """

    def get_file_signature(self):
        # Try all hdf5 files for now...
        return [r'.*\.hdf5']

    def create_coords(self, filenames):
        raise NotImplementedError("Todo!")

    def create_data_object(self, filenames, variable):
        from netCDF4 import Dataset
        from biggus import OrthoArrayAdapter
        from iris.cube import Cube, CubeList
        from iris.coords import DimCoord
        from iris.fileformats.netcdf import NetCDFDataProxy
        from datetime import datetime
        from os.path import basename
        from cis.time_util import cis_standard_time_unit

        cubes = CubeList()

        for f in filenames:
            # Open the file
            ds = Dataset(f)
            # E.g. 'NO2.COLUMN.VERTICAL.TROPOSPHERIC.CS30_BACKSCATTER.SOLAR'
            v = ds.variables[variable]
            # Get the coords
            lat = ds.variables['LATITUDE']
            lon = ds.variables['LONGITUDE']

            # Create a biggus adaptor over the data
            scale_factor = getattr(v, 'scale_factor', None)
            add_offset = getattr(v, 'add_offset', None)
            if scale_factor is None and add_offset is None:
                v_dtype = v.datatype
            elif scale_factor is not None:
                v_dtype = scale_factor.dtype
            else:
                v_dtype = add_offset.dtype
            proxy = NetCDFDataProxy(v.shape, v_dtype, f, variable,
                                    v._FillValue)
            a = OrthoArrayAdapter(proxy)

            # Just read the lat and lon in directly
            lat_coord = DimCoord(lat[:], standard_name='latitude', units='degrees', long_name=lat.VAR_DESCRIPTION)
            lon_coord = DimCoord(lon[:], standard_name='longitude', units='degrees', long_name=lon.VAR_DESCRIPTION)

            # Pull the date out of the filename
            fname = basename(f)
            dt = datetime.strptime(fname[:10], "%Y_%m_%d")
            t_coord = DimCoord(cis_standard_time_unit.date2num(dt), standard_name='time', units=cis_standard_time_unit)

            c = Cube(a, long_name=getattr(v, "VAR_DESCRIPTION", None), units=getattr(v, "VAR_UNITS", None),
                     dim_coords_and_dims=[(lat_coord, 0), (lon_coord, 1)])

            c.add_aux_coord(t_coord)

            # Close the file
            ds.close()

            cubes.append(c)

        merged = cubes.merge_cube()

        return merged
