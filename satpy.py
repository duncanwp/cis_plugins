from iris.coords import AuxCoord
from iris.cube import Cube


def scene_examples():
    from datetime import datetime
    from satpy.scene import Scene

    scn = Scene(
        platform_name="SNPP",
        sensor="viirs",
        start_time=datetime(2015, 4, 20, 12, 3),
        end_time=datetime(2015, 4, 20, 12, 10),
        base_dir="/home/a000680/data/polar_in/direct_readout/npp/lvl1/npp_20150420_1202_18019",
        reader="viirs_sdr"
    )

    scn.load(['M05', 'M08', 'M15'])

    met10scn = Scene(
        sensor="seviri",
        base_dir="/home/a000680/data/hrit/20150420",
        reader="hrit_msg"
    )
    met10scn.load([0.6, 0.8, 11.0])
    return


def scene_to_iris(scn, var_name):
    data = scn[var_name]
    area = data.info['area']
    units = data.info['units']
    lats = AuxCoord(area.lats, standard_name='latitude', units='degrees')
    lons = AuxCoord(area.lons, standard_name='longitude', units='degrees')
    cube = Cube(data, units=units, aux_coords_and_dims=[(lats, (0, 1)), (lons, (0, 1))], long_name=data.info['name'])
    return cube


def scene_to_cis(scn):
    from cis.data_io.Coord import Coord
    from cis.data_io.ungridded_data import Metadata, UngriddedData
    data = scn['M05']
    area = data.info['area']
    units = data.info['units']
    lats = Coord(
        area.lats, Metadata(standard_name='latitude', units='degrees'), 'y')
    lons = Coord(
        area.lons, Metadata(standard_name='longitude', units='degrees'), 'x')
    print(area.lons.info)
    ug = UngriddedData(data, Metadata(name=data.info['name'], units=units), [lats, lons])
    return ug


if __name__ == '__main__':
    pass
    # sub_seviri = ug_seviri.subset(x=[10, 12], y=[43, 45])
    # sub = ug.subset(x=[10, 12], y=[43, 45])
    #
    # col = sub_seviri.sampled_from(sub, kernel='nn_horizontal', h_sep=5.0)
    #
    # import matplotlib.pyplot as plt
    # import matplotlib as mpl
    # mpl.rcParams['agg.path.chunksize'] = 10000
    #
    # ll = UngriddedDataList([col[0], sub_seviri])
    # ax = ll.plot(how='histogram2d')
    # ax.set_xlim(0, 40)
    # ax.set_ylim(0, 40)
    # plt.show()
