platform_info = {
    'id' : 'ims',
    'location' : 'Institute of Marine Sciences, Morehead City, NC',
    'lat' : 34.724328,  # degrees true (-) south, (+) north
    'lon' : -76.751832, # degrees true (-) west, (+) east
    'mvar' : -9.7,      # degrees (-) west, (+) east
    'institution' : 'nccoos',
    # 
    'config_start_date' : '2007-09-20 00:00:00',
    'config_end_date' : '2008-12-11 00:00:00', # None or yyyy-mm-dd HH:MM:SS
    'packages' : ('pa0',),
    }
sensor_info = {
    'pa0' : { 'id' : 'sodar',
               'description' : 'Wind profile data',
               'raw_dir' : '/seacoos/data/nccoos/level0/ims/sodar',
               'raw_file_glob' : '*.dat',
               'proc_dir' : '/seacoos/data/nccoos/level1/ims/sodar',
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
    
