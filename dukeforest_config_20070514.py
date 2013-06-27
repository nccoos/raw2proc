platform_info = {
    'id' : 'dukeforest',
    'location' : 'Duke Forest, Chapel Hill, NC',
    'lat' : 35.971184,  # degrees true (-) south, (+) north
    'lon' : -79.094406, # degrees true (-) west, (+) east
    'mvar' : -9.7,      # degrees (-) west, (+) east
    'institution' : 'nccoos',
    # 
    'config_start_date' : '2007-05-14 00:00:00',
    'config_end_date' : '2007-07-11 00:00:00', # None or yyyy-mm-dd HH:MM:SS
    'packages' : ('pa0',),
    }
sensor_info = {
    'pa0' : { 'id' : 'sodar',
               'description' : 'Wind profile data',
               'raw_dir' : '/seacoos/data/nccoos/level0/dukeforest/sodar/store',
               'raw_file_glob' : '*.dat',
               'proc_dir' : '/seacoos/data/nccoos/level1/dukeforest/sodar',
               'process_module' : 'proc_remtech_rawdata_pa0',
               'utc_offset' : 4,         # hours offset to utc
               'min_altitude' : 30,      # meters
               'altitude_interval' : 20, # meters
               'num_altitudes' : 40,
               'sensor_elevation' : 30,   # meters
               # 'latest_dir' : '/seacoos/data/nccoos/latest_v2.0',
               # 'latest_vars' : ('time','lat','lon','z','u','v','w','echo'),
               },
    }
    
