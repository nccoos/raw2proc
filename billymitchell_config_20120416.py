platform_info = {
    'id' : 'billymitchell',
    'location' : 'Billy Mitchell Airfield, Frisco, NC',
    'lat' : 35.231691,  # degrees true (-) south, (+) north
    'lon' : -75.622614, # degrees true (-) west, (+) east
    'mvar' : -10.783333,      # degrees (-) west, (+) east
    'institution' : 'nccoos',
    'config_start_date' : '2012-04-16 19:30:00',
    'config_end_date' : '2012-12-31 23:59:59', # None or yyyy-mm-dd HH:MM:SS
    'packages' : ('sfas',),
    }
sensor_info = {
    'sfas' : { 'id' : 'sodar',
               'description' : 'Wind profile data',
               'raw_dir' : '/seacoos/data/nccoos/level0/'
                           'billymitchell/sodar1/mnd',
               'raw_file_glob' : '*.mnd',
               'proc_dir' : '/seacoos/data/nccoos/level1/'
                            'billymitchell/sodar1',
               'process_module' : 'proc_scintec_maindata_sfas',
               'utc_offset' : 0,         # hours offset to utc
               'min_altitude' : 10,      # meters
               'altitude_interval' : 5,  # meters
               'num_altitudes' : 39,
               'sensor_elevation' : 0,   # meters (runway elev is at 5.2 m)
               'plot_module' : 'billymitchell_sodar_plot', 
               'plot_names' : ('timeseries', 'wind_vectors', 'wind_barbs'), 
               },
    }
