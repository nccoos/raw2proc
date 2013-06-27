platform_info = {
 	    'id' : 'stones',
 	    'location' : 'Stones Bay, New River, NC',
 	    'lat' : 34.5962,   # degrees true (-) south, (+) north
 	    'lon' : -77.4120,  # degrees true (-) west, (+) east
 	    'mvar' : -9.38,    # degrees (-) west, (+) east
            'mean_water_depth': -4.0,
            'mean_water_depth_time_period': 'Not determined',
 	    'institution' : 'nccoos',
 	    #
 	    'config_start_date' : '2008-07-01 00:00:00',
 	    'config_end_date' : None, # None or yyyy-mm-dd HH:MM:SS
 	    'packages' : ('avp', 'met'),
 	    }

sensor_info = {
    'avp' : { 'id' : 'avp',
              'description' : 'Automated profiler data ctd and water quality',
              'raw_dir' : '/seacoos/data/nccoos/level0/stones/avp',
              'raw_file_glob' : '*.[Dd][Aa][Tt]',
              'proc_dir' : '/seacoos/data/nccoos/level1/stones/avp',
              'process_module' : 'proc_avp_ysi_6600_v2_CDL2',
              'utc_offset' : 5.,      # hours offset to Eastern Standard
              'bin_size' : 0.1,      # meters
              'nbins' : 150,          # max number of samples in profile
              'latest_dir' : '/seacoos/data/nccoos/latest_v2.0',
              'latest_vars' : ('time','lat','lon','z','wtemp','salin'),
              },
    'met' : { 'id' : 'met',
              'description' : 'Wind Data at Automated Vertical Profiler Station',
              'raw_dir' : '/seacoos/data/nccoos/level0/stones/met/',
              'raw_file_glob' : '*.[Ww][Nn][Dd]',
              'proc_dir' : '/seacoos/data/nccoos/level1/stones/met/',
              'process_module' : 'proc_avp_ascii_met',
              'utc_offset' : 5.,              # hours offset to Eastern Standard
              'anemometer_height' : 2.,      # meters
              'latest_dir' : '/seacoos/data/nccoos/latest_v2.0',
              'latest_vars' : ('time','lat','lon','z','u', 'v', 'wspd', 'wdir'),
             },
    }
