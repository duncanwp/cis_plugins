"""
Plugin for reading HYSPLIT trajectory files as CIS UngriddedData

(C) Paul Kim, Exeter University
"""
import logging
from cis.data_io.Coord import Coord, CoordList
from cis.data_io.products.AProduct import AProduct
from cis.data_io.ungridded_data import UngriddedData, Metadata, UngriddedCoordinates

# TODO add dtypes?
hysplit_default_var = ["TRAJECTORY_NO",
                       "GRID_NO",
                       "YEAR",
                       "MONTH",
                       "DAY",
                       "HOUR",
                       "MIN",
                       "F_HOUR",
                       "AGE",
                       "LAT",
                       "LON",
                       "ALT",
                       "PRESSURE"]


def get_file_metadata(fname):
    import linecache

    metadata = {}

    grid_metadata = linecache.getline(fname, 1).split()
    n_grids = int(grid_metadata[0])

    # Trajectory metadata present after grid metadata
    trajectory_metadata = linecache.getline(fname, n_grids+2).split()
    metadata['n_trajectories'] = int(trajectory_metadata[0])

    # Get starting lat/lon/alt of each trajectory
    metadata['trajectories'] = {}
    for t in range(metadata['n_trajectories']):
        tstart = linecache.getline(fname, n_grids+3+t).split()
        # Save trajectories according to numbering in file
        metadata['trajectories'][t+1] = (tstart[-3], tstart[-2], tstart[-1])

    metadata['data_start'] = n_grids + metadata['n_trajectories'] + 3

    # Get custom variable names
    variable_names = linecache.getline(fname, metadata['data_start']).split()[2:]
    metadata['labels'] = hysplit_default_var + variable_names
    metadata['custom_labels'] = variable_names

    linecache.clearcache()
    return metadata


def load_multiple_hysplit(fnames, variables=None):
    from cis.utils import add_element_to_list_in_dict, concatenate

    hdata = {}

    for filename in fnames:
        logging.debug("reading file: " + filename)

        # read in all trajectories
        # h_dict, key: trajectory starting lat/lon/altm value: dict containing trajectory data
        h_dict = load_hysplit(filename, variables)
        for traj in list(h_dict.keys()):
            if (traj in hdata):
                for var in list(h_dict[traj].keys()):
                    # TODO error appending masked array! add these manually
                    add_element_to_list_in_dict(hdata[traj], var, h_dict[traj][var])
                for var in list(hdata[traj].keys()):
                    hdata[traj][var] = concatenate(hdata[traj][var])
            else:
                hdata[traj] = h_dict[traj]

    return hdata


def load_hysplit(fname, variables=None):
    import numpy as np
    from numpy import ma
    from datetime import datetime, timedelta
    from cis.time_util import cis_standard_time_unit
    from cis.utils import add_element_to_list_in_dict, concatenate

    std_day = cis_standard_time_unit.num2date(0)

    fmetadata = get_file_metadata(fname)
    try:
        rawd = np.genfromtxt(fname,
                             skip_header=fmetadata['data_start'],
                             dtype=np.float64,
                             usemask=True)
    except (StopIteration, IndexError) as e:
        raise IOError(e)

    data_dict = {}
    # Get data for one trajectory at a time
    for t in range(1, fmetadata['n_trajectories']+1):
        tdata_dict = {}

        trajectory_data = rawd[rawd[:,hysplit_default_var.index('TRAJECTORY_NO')] == t]
        # Convert time from each row to standard time
        for trajectory in trajectory_data:
            day = datetime((int(trajectory[2]) + 2000), # TODO Dan: is it okay to assume this?
                            int(trajectory[3]),
                            int(trajectory[4]))
            sday = float((day - std_day).days)
            td = timedelta(hours=int(trajectory[5]), minutes=int(trajectory[6]))
            fractional_day = td.total_seconds()/(24.0*60.0*60.0)
            dt = sday + fractional_day
            add_element_to_list_in_dict(tdata_dict, 'DATETIMES', [dt])
        # Clean up data
        tdata_dict['DATETIMES'] = ma.array(concatenate(tdata_dict['DATETIMES'])) # TODO mask is only one value

        # Add other default data
        tdata_dict['LAT'] = trajectory_data[:,hysplit_default_var.index('LAT')]
        tdata_dict['LON'] = trajectory_data[:,hysplit_default_var.index('LON')]
        tdata_dict['ALT'] = trajectory_data[:,hysplit_default_var.index('ALT')]
        tdata_dict['PRESSURE'] = trajectory_data[:, hysplit_default_var.index('PRESSURE')]
        # TODO any other default variables to add?

        # If variables set, fetch only set variables
        if variables is not None:
            for key in variables:
                try:
                    tdata_dict[key] = trajectory_data[:,fmetadata['labels'].index(key)]
                except ValueError:
                    raise InvalidVariableError(key + "does not exist in " + fname)
        # Else, return all variables in file
        else:
            for label in fmetadata['custom_labels']:
                try:
                    tdata_dict[label] = trajectory_data[:,fmetadata['labels'].index(label)]
                except ValueError:
                    raise InvalidVariableError(key + " does not exist in " + fname)

        # TODO trajectory keys are tuples of lat/long/alt
        tkey = fmetadata['trajectories'][t]
        data_dict[tkey] = tdata_dict

    return data_dict


class HYSPLIT(AProduct):
    def get_file_signature(self):
        return [r'.*\.dat']

    def _create_coord_list(self, filenames, data=None):
        from cis.data_io.ungridded_data import Metadata
        from cis.time_util import cis_standard_time_unit as ct

        if data is None:
            data_all = load_multiple_hysplit(filenames)
            # TODO only using first trajectory
            data = data_all[list(data_all.keys())[0]]

        coords = CoordList()

        latM = Metadata(name="Latitude", shape=(len(data),), units="degrees_north",
                        range=(-90,90), standard_name='latitude')
        lonM = Metadata(name="Longitude", shape=(len(data),), units="degrees_east",
                        range=(-180,180), standard_name='longitude')
        altM = Metadata(name="Altitude", shape=(len(data),), units="meters", standard_name='altitude')
        presM = Metadata(name="Pressure", shape=(len(data),), units="hPa", standard_name='air_pressure')
        timeM = Metadata(name="DateTime", standard_name="time", shape=(len(data),), units=str(ct))

        coords.append(Coord(data['LAT'], latM))
        coords.append(Coord(data['LON'], lonM))
        coords.append(Coord(data['ALT'], altM))
        coords.append(Coord(data['PRESSURE'], presM))
        coords.append(Coord(data['DATETIMES'], timeM, "X")) # TODO Why X axis?

        return coords

    def create_coords(self, filenames, variable=None):
        return UngriddedCoordinates(self._create_coord_list(filenames))

    def create_data_object(self, filenames, variable):
        from cis.exceptions import InvalidVariableError

        try:
            data_obj_all = load_multiple_hysplit(filenames, [variable])
            # TODO only using first trajectory
            data_obj = data_obj_all[list(data_obj_all.keys())[0]]
        except ValueError:
            raise InvalidVariableError(variable + " does not exist in " + str(filenames))

        coords = self._create_coord_list(filenames, data_obj)

        objM = Metadata(name=variable,
                        long_name=variable,
                        shape=(len(data_obj)),
                        missing_value=-999.0)
        return UngriddedData(data_obj[variable], objM, coords)
