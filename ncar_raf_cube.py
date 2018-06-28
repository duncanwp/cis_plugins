import logging
import os

import numpy as np

from cis.exceptions import FileFormatError
from cis.data_io.products import AProduct
from cis.utils import add_to_list_if_not_none, listify
from cis.data_io.netcdf import get_metadata, get_netcdf_file_attributes, read_many_files_individually, \
    get_netcdf_file_variables
from cis.data_io.products.NCAR_NetCDF_RAF import NCAR_NetCDF_RAF_variable_name_selector


class NCAR_NetCDF_RAF_Cube(AProduct):
    """
    Data product for NCAR-RAF NetCDF files. This includes the subset of GASSP (which is its major use case)
    """

    # Set the priority to be higher than the other netcdf file types
    priority = 20

    # Name of the attribute in GASSP that defines the GASSP version
    GASSP_VERSION_ATTRIBUTE_NAME = "GASSP_Version"

    # Name of the attribute in NCAR_RAF that defines the converntion
    NCAR_RAF_CONVENTIONS_ATTRIBUTE_NAME = "Conventions"
    # Known NCAR RAF Converntions
    NCAR_RAF_KNOWN_CONVENTION = "NCAR-RAF/nimbus"
    # NCAR RAF Convention version name
    NCAR_RAF_CONVENTION_VERSION_ATTRIBUTE_NAME = "ConventionsVersion"

    def __init__(self, variable_selector_class=NCAR_NetCDF_RAF_variable_name_selector):
        """
        Setup NCAR RAF data product, allow a different variable selector class if needed
        :param variable_selector_class: the class to use for variable selection
        :return:nothing
        """
        super(NCAR_NetCDF_RAF_Cube, self).__init__()
        self.variableSelectorClass = variable_selector_class
        self.valid_dimensions = ["Time"]

    def get_file_signature(self):
        """
        Get the filename possibilities allowed for NCAR-RAF data
        :return: list of regular expressions for ncar raf data
        """
        return [r'.*\.nc$']

    def _get_file_format(self, filename):
        """
        Get the file type and any errors
        :param filename: the filename to read the type of
        :return: filetype
        :raises: FileFormatError if there is an error
        """
        if not os.path.isfile(filename):
            raise FileFormatError(["File does not exist"])
        try:
            attributes = get_netcdf_file_attributes(filename)
        except (RuntimeError, IOError) as ex:
            raise FileFormatError(["File is unreadable", ex.args[0]])

        attributes_lower = {attr.lower(): val for attr, val in list(attributes.items())}
        if self.GASSP_VERSION_ATTRIBUTE_NAME.lower() in attributes_lower:
            file_type = "NetCDF/GASSP/{}".format(attributes_lower[self.GASSP_VERSION_ATTRIBUTE_NAME.lower()])

        elif self.NCAR_RAF_CONVENTIONS_ATTRIBUTE_NAME.lower() in attributes_lower:
            ncarraf_convention = attributes_lower[self.NCAR_RAF_CONVENTIONS_ATTRIBUTE_NAME.lower()]
            version = ""
            if self.NCAR_RAF_CONVENTION_VERSION_ATTRIBUTE_NAME.lower() in attributes_lower:
                version = "/{}".format(attributes_lower[self.NCAR_RAF_CONVENTION_VERSION_ATTRIBUTE_NAME.lower()])
            if not ncarraf_convention == self.NCAR_RAF_KNOWN_CONVENTION:
                raise FileFormatError(["NCAR-RAF convention unknown, expecting '{}' was '{}'"
                                      .format(self.NCAR_RAF_KNOWN_CONVENTION, ncarraf_convention)])
            file_type = "NetCDF/{}{}".format(ncarraf_convention, version)

        else:
            raise FileFormatError(["File does not appear to be NCAR RAF or GASSP. No attributes for either '{}' or '{}'"
                                  .format(self.GASSP_VERSION_ATTRIBUTE_NAME, self.NCAR_RAF_CONVENTIONS_ATTRIBUTE_NAME)])

        return file_type

    def get_file_type_error(self, filename):
        """
        Test that the file is of the correct signature
        :param filename: the file name for the file
        :return: list fo errors or None
        """
        try:
            self._get_file_format(filename)
            return None
        except FileFormatError as ex:
            return ex.error_list

    def _load_data_definition(self, filenames):
        """
        Load the definition of the data
        :param filenames: filenames from which to load the data
        :return: variable selector containing the data definitions
        """
        variables_list = [get_netcdf_file_variables(f) for f in filenames]
        attributes = [get_netcdf_file_attributes(f) for f in filenames]

        variable_selector = self.variableSelectorClass(attributes, variables_list)
        return variable_selector

    def _load_data(self, filenames, variable):
        """
        Open the file and find the correct variables to load in
        :param filenames: the filenames to load
        :param variable: an extra variable to load
        :return: a list of load data and the variable selector used to load name it
        """

        variable_selector = self._load_data_definition(filenames)

        variables_list = [variable_selector.time_variable_name]
        add_to_list_if_not_none(variable_selector.latitude_variable_name, variables_list)
        add_to_list_if_not_none(variable_selector.longitude_variable_name, variables_list)
        add_to_list_if_not_none(variable_selector.altitude_variable_name, variables_list)
        add_to_list_if_not_none(variable_selector.pressure_variable_name, variables_list)

        logging.info("Listing coordinates: " + str(variables_list))
        add_to_list_if_not_none(variable, variables_list)

        data_variables = read_many_files_individually(filenames, variables_list)

        return data_variables, variable_selector

    def _create_coordinates_list(self, data_variables, variable_selector):
        """
        Create a co-ordinate list for the data
        :param data_variables: the load data
        :param variable_selector: the variable selector for the data
        :return: a list of coordinates
        """
        coords = []

        # Time
        time_coord = self._create_time_coord(variable_selector.time_stamp_info, variable_selector.time_variable_name,
                                             data_variables)
        coords.append(time_coord)

        # Lat and Lon
        # Multiple points counts for multiple files
        points_count = [np.product(var.shape) for var in data_variables[variable_selector.time_variable_name]]
        if variable_selector.station:
            lat_coord = self._create_fixed_value_coord("Y", variable_selector.station_latitude, "degrees_north",
                                                       points_count, "latitude")
            lon_coord = self._create_fixed_value_coord("X", variable_selector.station_longitude, "degrees_east",
                                                       points_count, "longitude")
        else:
            lat_coord = self._create_coord("Y", variable_selector.latitude_variable_name, data_variables, "latitude")
            lon_coord = self._create_coord("X", variable_selector.longitude_variable_name, data_variables, "longitude")
        coords.append(lat_coord)
        coords.append(lon_coord)

        # Altitude
        if variable_selector.altitude is None:
            altitude_coord = self._create_coord("Z", variable_selector.altitude_variable_name, data_variables,
                                                "altitude")
        else:
            altitude_coord = self._create_fixed_value_coord("Z", variable_selector.altitude, "meters", points_count,
                                                            "altitude")
        coords.append(altitude_coord)

        # Pressure
        if variable_selector.pressure_variable_name is not None:
            coords.append(
                self._create_coord("P", variable_selector.pressure_variable_name, data_variables, "air_pressure"))
        return coords

    def create_coords(self, filenames, variable=None):
        """
        Reads the coordinates and data if required from the files
        :param filenames: List of filenames to read coordinates from
        :param variable: load a variable for the data
        :return: Coordinates
        """
        from iris.cube import Cube
        from iris.coords import DimCoord
        from cis.data_io.netcdf import read
        from cis.utils import concatenate

        data_variables, variable_selector = self._load_data(filenames, variable)

        aux_coords = self._create_coordinates_list(data_variables, variable_selector)
        dim_coords = [(DimCoord(np.arange(len(aux_coords[0].points)), var_name='obs'), (0,))]

        if variable is None:
            raise ValueError("Must specify variable")

        aux_coord_name = variable_selector.find_auxiliary_coordinate(variable)
        if aux_coord_name is not None:
            # We assume that the auxilliary coordinate is the same shape across files
            v = read(filenames[0], [aux_coord_name])[aux_coord_name]
            aux_meta = get_metadata(v)
            # We have to assume the shape here...
            dim_coords.append((DimCoord(v[:], var_name=aux_coord_name, units=aux_meta.units,
                                    long_name=aux_meta.long_name), (1,)))

        cube_meta = get_metadata(data_variables[variable][0])
        return Cube(concatenate([d[:] for d in data_variables[variable]]),
                    units=cube_meta.units, var_name=variable, long_name=cube_meta.long_name,
                    dim_coords_and_dims=dim_coords, aux_coords_and_dims=[(c, (0,)) for c in aux_coords])

    def create_data_object(self, filenames, variable):
        """
        Load the variable with it coordinates from the files
        :param filenames: filenames of the file
        :param variable: the variable to load
        :return: Data object
        """
        return self.create_coords(filenames, variable)

    def _create_coord(self, coord_axis, data_variable_name, data_variables, standard_name):
        """
        Create a coordinate for the co-ordinate list
        :param coord_axis: axis of the coordinate in the coords
        :param data_variable_name: the name of the variable in the data
        :param data_variables: the data variables
        :param standard_name: the standard name it should have
        :return: a coords object
        """
        from iris.coords import AuxCoord
        from cis.utils import concatenate
        data = concatenate([d[:] for d in data_variables[data_variable_name]])

        m = get_metadata(data_variables[data_variable_name][0])

        return AuxCoord(data, units=m.units, standard_name=standard_name)

    def _create_time_coord(self, timestamp, time_variable_name, data_variables, coord_axis='T', standard_name='time'):
        """
        Create a time coordinate, taking into account the fact that each file may have a different timestamp.
        :param timestamp: Timestamp or list of timestamps for
        :param time_variable_name: Name of the time variable
        :param data_variables: Dictionary containing one or multiple netCDF data variables for each variable name
        :param coord_axis: Axis, default 'T'
        :param standard_name: Coord standard name, default 'time'
        :return: Coordinate
        """
        from iris.coords import AuxCoord
        from six.moves import zip_longest
        from cis.time_util import convert_time_using_time_stamp_info_to_std_time as convert, cis_standard_time_unit
        from cis.utils import concatenate

        timestamps = listify(timestamp)
        time_variables = data_variables[time_variable_name]
        time_data = []
        # Create a coordinate for each separate file to account for differing timestamps
        for file_time_var, timestamp in zip_longest(time_variables, timestamps):
            metadata = get_metadata(file_time_var)
            if timestamp is not None:
                time_d = convert(file_time_var[:], metadata.units, timestamp)
            else:
                time_d = metadata.units.convert(file_time_var[:], cis_standard_time_unit)
            time_data.append(time_d)

        return AuxCoord(concatenate(time_data), standard_name=standard_name, units=cis_standard_time_unit)

    def _create_fixed_value_coord(self, coord_axis, values, coord_units, points_counts, coord_name):
        """
        Create a coordinate with a fixed value
        :param coord_axis: Axis of the coordinate in the coords
        :param coord_name: The name of the coordinate
        :param coord_units: The units for the coordinate
        :param points_counts: Number of points for this coordinate, or list of sizes for multiple files
        :param values: Value of coordinate, or list of values for multiple files
        :return:
        """
        from iris.coords import AuxCoord

        all_points = np.array(listify(values))

        return AuxCoord(all_points, units=coord_units, standard_name=coord_name)

    def get_variable_names(self, filenames, data_type=None):
        """
        Get a list of available variable names
        This can be overridden in specific products to improve on this
        """

        selector = self._load_data_definition(filenames)
        return selector.get_variable_names_which_have_time_coord()

    def get_file_format(self, filename):
        """
        Return the file format, in general this string is parent format/specific instance/version
        e.g. NetCDF/GASSP/1.0
        :param str filename: Filename of a an example file from the dataset
        :returns: File format, of the form parent format/specific instance/version
        :rtype: str
        :raises: FileFormatError if files type is not determinable
        """
        return self._get_file_format(filename)
