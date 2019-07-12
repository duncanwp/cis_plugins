#import logging
from cis.data_io.Coord import Coord, CoordList
from cis.data_io.products.AProduct import AProduct
from cis.data_io.ungridded_data import UngriddedData, Metadata, UngriddedCoordinates


class HYSPLIT(AProduct):
    def get_file_signature(self):
        return [r'.*\.dat']

    def _create_coord_list(self, filenames, data=None):
        from cis.data_io.ungridded_data import Metadata
        from cis.time_util import cis_standard_time_unit as ct
        import numpy as np

        if data is None:
            data = load_multiple_hysplit(filenames) # TODO error handling

        coords = CoordList()

        #print(data['DATETIMES'])
        latM = Metadata(standard_name="latitude", shape=(len(data['LAT']),), units="degrees_north", range=(-90,90))
        lonM = Metadata(standard_name="longitude", shape=(len(data['LON']),), units="degrees_east", range=(-180,180))
        altM = Metadata(standard_name="altitude", shape=(len(data['ALT']),), units="m")
        timeM = Metadata(standard_name="time", shape=(len(data['DATETIMES']),), units=str(ct))
        #timeM = Metadata(name="DateTime", standard_name="time", shape=(len(data['DATETIMES']),), units=str(ct))
        pressM = Metadata(standard_name="air_pressure", shape=(len(data['PRESSURE']),), units="Pa")
        #start_timeM = Metadata(name="start_time", standard_name="forecast_reference_time", shape=(len(data['STARTING_TIME']),), units=str(ct))
        #start_heightM = Metadata(name="start_height", shape=(len(data['STARTING_HEIGHT']),), units="meters")
        #station_noM = Metadata(name="station_no", standard_name="institution", shape=(len(data['STATION_NO']),))

        coords.append(Coord(data['DATETIMES'], timeM))
        coords.append(Coord(data['PRESSURE'], pressM))
        coords.append(Coord(data['LAT'], latM))
        coords.append(Coord(data['LON'], lonM))
        coords.append(Coord(data['ALT'], altM))
        #coords.append(Coord(data['STARTING_TIME'], start_timeM))
        #coords.append(Coord(data['STARTING_HEIGHT'], start_heightM))
        #coords.append(Coord(data['STATION_NO'], station_noM))

        return coords

    def create_coords(self, filenames, variable=None):
        return UngriddedCoordinates(self._create_coord_list(filenames))

    def create_data_object(self, filenames, variable):
        from cis.exceptions import InvalidVariableError, CISError
        import numpy as np

        try:
            data_obj = load_multiple_hysplit(filenames, [variable])
        except ValueError:
            raise InvalidVariableError(variable + " does not exist in " + str(filenames))
        except EOFError as e:
            raise CISError(e)
        except IOError as e:
            raise CISError(e) # TODO

        coords = self._create_coord_list(filenames, data_obj)

        # WRITE STANDARD NAME GUESSER HERE
        if variable == "PRESSURE":
            variable = "air_pressure"
        elif variable == "RELHUMID":
            variable = "relative_humidity"

        objM = Metadata(name=variable,
                        standard_name=variable,
                        long_name=variable,
                        shape=(len(data_obj[variable]),),
                        missing_value=-99999.0)
        #objM.standard_name = None

        #print((len(data_obj[variable]),))
        return UngriddedData(data_obj[variable], objM, coords)


def _convert_to_cis_time(year, month, day, hour, minute=0):
    '''
    Convert a HYSPLIT time format to CIS standard time.

    :param year: an integer year (starting at 1)
    :param mongth: an integer month (1-12)
    :param day: an integer day of the month (starting at 1)
    :param hour: an integer hour

    :returns: The CIS standard time equivalent
    '''
    from datetime import datetime, timedelta
    from cis.time_util import cis_standard_time_unit

    # CIS time starts at 1600-01-01 00:00:00
    std_day = cis_standard_time_unit.num2date(0)

    datetime_day = datetime(year, month, day)
    cis_day = float((datetime_day - std_day).days)

    td = timedelta(hours=hour, minutes=minute)
    fractional_day = td.total_seconds()/(24.0*60.0*60.0)

    return cis_day + fractional_day

def _get_file_metadata(fname):
    '''
    Fetch and load HYSPLIT file metadata into a dictionary.
    Returned dictionary key-value pairs:
        (key)              : (value)
        n_trajectories     : number of trajectories
        trajectory_ids     : start time/lat/lon/alt of each trajectory
        data_start         : line in file where data begins (line 1 = 0)
        labels             : all the column headings in the file
        custom_labels      : the custom column headings only

    :param fname: The path to the data file
    :return: The file metadata dictionary
    '''
    import linecache

    metadata = {}

    grid_metadata = linecache.getline(fname, 1).split()
    n_grids = int(grid_metadata[0])

    # Trajectory metadata present after grid metadata
    trajectory_metadata = linecache.getline(fname, n_grids+2).split()
    metadata['n_trajectories'] = int(trajectory_metadata[0])

    # Get starting time/lat/lon/alt of each trajectory
    metadata['trajectory_ids'] = {}
    for t in range(metadata['n_trajectories']):
        tstart = linecache.getline(fname, n_grids+3+t).split()

        # Get trajectory start time as CIS standard time
        start_time = _convert_to_cis_time(int(tstart[0]),
                                          int(tstart[1]),
                                          int(tstart[2]),
                                          int(tstart[3]))

        # Save trajectories according to start time/lat/lon/alt
        metadata['trajectory_ids'][t+1] = (start_time, tstart[-3], tstart[-2], tstart[-1])

    metadata['data_start'] = n_grids + metadata['n_trajectories'] + 3

    # Get custom variable names
    variable_names = linecache.getline(fname, metadata['data_start']).split()[1:]
    metadata['labels'] = __default_variables__ + variable_names
    metadata['custom_labels'] = variable_names

    linecache.clearcache()
    return metadata

def _dict_append(data_dict, key, data):
    '''
    Append masked arrays in a dictionary. If the dictionary array
    doesn't exist, create it.

    :param data_dict: The dictionary
    :param key: The element to append to
    :param data: The data to append
    '''
    import numpy.ma as ma

    if key in data_dict:
        data_dict[key] = ma.append(data_dict[key], data)
    else:
        data_dict[key] = data

def _load_hysplit(fname, variables=None):
    '''
    Load HYSPLIT data from a file into a dictionary. Data for each
    trajectory is concatenated by field.

    Default fields: lat, lon, alt, station number, starting alt.
    Custom fields: either determined by given variables or the variables
    present in the file.

    IMPORTANT: HYSPLIT has a two digit year i.e. 2016 = 16 and
    1979 = 79. Because of this, this function is only valid for years
    1946 to 2045 (inclusive)!

    :param fname: The path to the data file
    :param variables: The custom variables to be loaded
    :return: The file data dictionary
    '''
    import numpy as np
    import numpy.ma as ma

    try:
        file_metadata = _get_file_metadata(fname)
    except IndexError as e:
        raise IOError("Error reading metadata for '" + fname + "':" + str(e))

    # Read data into NumPy arrays
    try:
        rawd = np.genfromtxt(fname,
                             skip_header=file_metadata['data_start'],
                             dtype=np.float64,
                             usemask=True)
    except (StopIteration, IndexError, ValueError) as e:
        raise IOError("Error reading '" + fname + "': " + str(e))

    file_dict = {}

    # Get data for one trajectory at a time
    for t in range(1, 2):
        # Get all data rows for trajectory t
        trajectory_data = rawd[rawd[:,__default_variables__.index('TRAJECTORY_NO')] == t]

        # Convert time from each row to standard time
        datetimes = np.empty(len(trajectory_data))
        for row_num, row in enumerate(trajectory_data):
            year   = int(row[__default_variables__.index('YEAR')])
            month  = int(row[__default_variables__.index('MONTH')])
            day    = int(row[__default_variables__.index('DAY')])
            hour   = int(row[__default_variables__.index('HOUR')])
            minute = int(row[__default_variables__.index('MIN')])

            # Only valid for data in range 1946 to 2045 (inclusive)!
            if year > 45:
                year += 1900
            else:
                year += 2000

            datetimes[row_num] = _convert_to_cis_time(year, month, day, hour, minute)

        # Mask any negative values for CIS standard time
        _dict_append(file_dict, 'DATETIMES', ma.masked_less(datetimes, 0.0))

        # Add other default data
        _dict_append(file_dict, 'LAT', trajectory_data[:,__default_variables__.index('LAT')])
        _dict_append(file_dict, 'LON', trajectory_data[:,__default_variables__.index('LON')])
        _dict_append(file_dict, 'ALT', trajectory_data[:,__default_variables__.index('ALT')])

        # If variables set, fetch only set variables
        try:
            if variables is not None:
                for key in variables:
                    tmp_t_data = trajectory_data[:,file_metadata['labels'].index(key)]

                    # TODO: changed name of PRESSURE to air_pressure
                    if key == "PRESSURE":
                        key = "air_pressure"
                    elif key == "RELHUMID":
                        key = "relative_humidity"

                    _dict_append(file_dict,
                                 key,
                                 tmp_t_data)
            # Else, return all variables in file
            else:
                for label in file_metadata['custom_labels']:
                    _dict_append(file_dict,
                                 label,
                                 trajectory_data[:,file_metadata['labels'].index(label)])
        except ValueError:
            raise ValueError(key + "does not exist in '" + fname + "'")

        # Add trajectory id information for smarter subsetting
        trajectory_id = file_metadata['trajectory_ids'][t]
        starting_time = trajectory_id[0]
        starting_location = (trajectory_id[1], trajectory_id[2])
        starting_height = trajectory_id[3]

        # Trajectory starting time
        fill = np.full(len(trajectory_data), starting_time)
        starting_time_data = ma.masked_less(fill, 0.0)
        _dict_append(file_dict, 'STARTING_TIME', starting_time_data)

        # Trajectory starting location
        if starting_location in __station_lookup__:
            station_number = __station_lookup__[starting_location][0]
            fill = np.full(len(trajectory_data), float(station_number))
            station_data = ma.array(fill, mask=False)
        # If starting location not found, set station number as 0
        else:
            fill = np.full(len(trajectory_data), 0)
            station_data = ma.array(fill, mask=False)
        _dict_append(file_dict, 'STATION_NO', station_data)

        # Trajectory starting height
        fill = np.full(len(trajectory_data), float(starting_height))
        starting_height_data = ma.array(fill, mask=False)
        _dict_append(file_dict, 'STARTING_HEIGHT', starting_height_data)

    return file_dict

def _check_files(fnames, variables):
    '''
    Check whether all given files have the required fields. If there is
    a mismatch of fields, the data is likely to also be mismatched. If
    no variables are given, all files must have same fields otherwise
    all files can have different fields as long as they include the
    required fields.

    :param fnames: The filename list
    :param variables: The required variables
    :return: Boolean for success
    '''
    #logging.debug("Checking files.")

    # If no variables set, use first file as standard
    if variables is None:
        #logging.debug("No variables given. Using '" + fnames[0] + "' as standard")
        expected_variables = _get_file_metadata(fnames[0])['labels']
    else:
        expected_variables = __default_variables__ + variables

    for fname in fnames:
        # If no variables set, all files must have same fields
        if variables is None:
            if _get_file_metadata(fname)['labels'] != expected_variables:
                return False
        # If variables set, check required variables are present in each file
        else:
            file_variables = _get_file_metadata(fname)['labels']
            for variable in expected_variables:
                if variable not in file_variables:
                    return False

    return True

def load_multiple_hysplit(fnames, variables=None):
    '''
    Load HYSPLIT data from multiple files into a single dictionary. Data
    across files and trajectories is concatenated by field.

    :param fnames: The paths to the data files in a list
    :param variables: The custom variables to be loaded (default is all)
    :return: The data dictionary
    '''
    import numpy.ma as ma
    import linecache

    hysplit_data = {}

    if not _check_files(fnames, variables):
        raise IOError("Given files don't have matching fields!")

    for filename in fnames:
        #logging.debug("Reading file: " + filename)

        # Read trajectories from file
        file_dict = _load_hysplit(filename, variables)

        # Add data from file to hysplit_data dictionary
        for field in file_dict:
            _dict_append(hysplit_data, field, file_dict[field])

    return hysplit_data


__default_variables__ = ['TRAJECTORY_NO',
                         'GRID_NO',
                         'YEAR',
                         'MONTH',
                         'DAY',
                         'HOUR',
                         'MIN',
                         'F_HOUR',
                         'AGE',
                         'LAT',
                         'LON',
                         'ALT']

__station_lookup__ = {
	( '78.906',   '11.888'): [ 1, 'ZEP', 'Zeppelin'],
	( '81.600',  '-16.670'): [ 2, 'NRD', 'Station Nord'],
	( '82.500',  '-62.300'): [ 3, 'ALT', 'Alert'],
	( '71.320', '-156.616'): [ 4, 'BRW', 'Barrow'],
	( '71.600',  '128.890'): [ 5, 'TIK', 'Tiksi'],
	( '58.800',   '17.383'): [ 6, 'ASP', 'Aspvreten'],
	( '58.383',    '8.250'): [ 7, 'BIR', 'Birkenes'],
	( '67.967',   '24.117'): [ 8, 'PAL', 'Pallas'],
	( '55.370',   '21.030'): [ 9, 'PLA', 'Preila'],
	( '61.850',   '24.283'): [10, 'SMR', 'Hyytiala (SMEAR II)'],
	( '56.017',   '13.150'): [11, 'VHL', 'Vavihill'],
	( '58.370',   '26.740'): [12, 'TTU', 'Tartu'],
	( '54.643',	  '25.183'): [13, 'VIL', 'Vilnius'],
	( '67.767',   '29.583'): [14, 'VRO', 'Varrio'],
	( '53.000',    '7.950'): [15, 'BOS', 'Bosel'],
	( '46.967',   '19.317'): [16, 'KPO', 'K-Puszta'],
	( '51.540',   '12.930'): [17, 'MPZ', 'Melptiz'],
	( '49.580',   '15.250'): [18, 'OBK', 'Kosetice'],
	( '47.800',   '11.010'): [19, 'HPB', 'Hohenpeissenberg'],
	( '52.800',   '10.756'): [20, 'WAL', 'Waldhof'],
	( '50.127',   '14.385'): [21, 'PRG', 'Prague'],
	( '51.971',    '4.927'): [22, 'CBW', 'Cabauw'],
	( '51.567',   '-1.317'): [23, 'HWL', 'Harwell'],
	( '51.521',  '-0.2135'): [24, 'NKEN', 'North Kensington'],
	( '53.326',   '-9.904'): [25, 'MHD', 'Mace Head'],
	( '45.779',    '4.882'): [26, 'LYN', 'Lyon'],
	( '40.456',   '-3.730'): [27, 'MDR', 'Madrid'],
	( '48.718',    '2.207'): [28, 'PAR', 'Paris (SITRA)'],
	( '35.330',   '25.670'): [29, 'FKL', 'Finokalia'],
	( '45.820',    '8.630'): [30, 'IPR', 'JRC-Ispra'],
	( '42.969',    '9.380'): [31, 'CAP', 'Cap Corse (CHARMEX Supersite'],
	( '41.779',    '2.358'): [32, 'MNY', 'Montseny'],
	( '36.830',   '21.704'): [33, 'NEO', 'Navarino Observatory'],
	( '-7.970',  '-14.405'): [34, 'ASI', 'Ascension Island'],
	( '24.700',   '54.659'): [35, 'MCO', 'Maarco, UAE (Arabian Gulf)'],
	( '37.164',   '-3.605'): [36, 'GRA', 'Granada'],
	( '48.562',    '5.506'): [37, 'OPE', 'Observatoire Perenne de l\'Environnement'],
	( '50.572',   '12.999'): [38, 'ABU', 'Annaberg-Buchholz'],
	( '53.167',   '13.033'): [39, 'NGW', 'Neuglobsow'],
	( '50.661',   '14.040'): [40, 'LMO', 'L.mesto'],
	( '50.304',    '6.001'): [41, 'VLM', 'Vielsalm'],
	( '37.991',   '23.810'): [42, 'ATH', 'Athens'],
	( '40.336',   '18.125'): [43, 'LEC', 'LecceECO'],
	( '36.072',   '14.218'): [44, 'GIO', 'Giordan Lighthouse'],
	( '36.538',  '126.330'): [45, 'AYO', 'Anmyeondo, South Korea'],
	( '51.036',   '13.731'): [46, 'DRE', 'Dresden Winckelmannstrasse'],
	('-70.666',   '-8.266'): [47, 'NMY', 'Neumayer'],
	( '28.428',   '77.151'): [48, 'GPA', 'GualPahari'],
	('-22.980',   '14.374'): [49, 'WVB', 'Walvis Bay (Airport)'],
	('-15.942',   '-5.667'): [50, 'STH', 'St Helena'],
	('-23.562',   '15.041'): [51, 'GOB', 'Gobabeb'],
	('-22.095',   '14.260'): [52, 'HEN', 'Henties Bay'],
	( '32.121',  '118.953'): [53, 'NAN', 'Nanjing (SORPES)'],
	( '25.800',   '84.200'): [54, 'BAL', 'Balia'],
	( '26.183',   '91.733'): [55, 'GUW', 'Guwahati'],
	( '45.772',    '2.966'): [56, 'PDD', 'Puy de Dome'],
	( '47.917',    '7.917'): [57, 'SSL', 'Schauinsland'],
	( '47.417',   '10.983'): [58, 'ZSF', 'Zugspitze'],
	( '46.548',    '7.985'): [59, 'JFJ', 'Jungfraujoch'],
	( '42.180',   '23.585'): [60, 'BEO', 'Moussala'],
	( '44.200',   '10.700'): [61, 'CMN', 'Monte Cimone'],
	( '19.540', '-155.580'): [62, 'MLO', 'Mauna Loa Observatory'],
	( '63.427',   '13.077'): [63, 'ARE', 'Are'],
	( '72.596',  '-38.422'): [64, 'SMT', 'Summit'],
	( '42.937',    '0.142'): [65, 'PIC', 'Pic du Midi'],
	( '28.309',  '-16.499'): [66, 'IZA', 'Izana'],
	( '27.958',   '86.815'): [67, 'NEP', 'Nepal Climate Observatory Pyramid'],
	('-16.350',  '-68.131'): [68, 'CHAC', 'Mount Chacaltaya'],
	('-72.012',    '2.535'): [69, 'TRO', 'Trollhaugen']
}
