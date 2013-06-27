platform_info = {
 	    'id' : 'hampton',
 	    'location' : 'Hampton Shoals, Neuse River, NC',
 	    'lat' : 35.0184,  # degrees true (-) south, (+) north
 	    'lon' : -76.9409, # degrees true (-) west, (+) east
 	    'mvar' : -9.80,   # degrees (-) west, (+) east
 	    'institution' : 'nccoos',
 	    #
 	    'config_start_date' : '2008-09-30 00:00:00',
 	    'config_end_date' : '2010-10-19 00:00:00', # None or yyyy-mm-dd HH:MM:SS
 	    'packages' : ('avp', 'met'),
 	    }

sensor_info = {
    'avp' : { 'id' : 'avp',
              'description' : 'Automated profiler data ctd and water quality',
              'raw_dir' : '/seacoos/data/nccoos/level0/hampton/avp/',
              'raw_file_glob' : '*.dat',
              'proc_dir' : '/seacoos/data/nccoos/level1/hampton/avp/',
              'process_module' : 'proc_avp_ysi_6600_v1_CDL2',
              'utc_offset' : 5.,     # hours offset to Eastern Standard
              'bin_size' : 0.1,      # meters
              'nbins' : 150,          # max number of samples in profile
              'latest_dir' : '/seacoos/data/nccoos/latest_v2.0',
              'latest_vars' : ('time','lat','lon','z','wtemp','salin'),
              },
    'met' : { 'id' : 'met',
              'description' : 'Wind Data at Automated Vertical Profiler Station',
              'raw_dir' : '/seacoos/data/nccoos/level0/hampton/met/',
              'raw_file_glob' : '*.wnd',
              'proc_dir' : '/seacoos/data/nccoos/level1/hampton/met/',
              'process_module' : 'proc_avp_ascii_met',
              'utc_offset' : 5.,             # hours offset to Eastern Standard
              'anemometer_height' : 2.,      # meters
              'latest_dir' : '/seacoos/data/nccoos/latest_v2.0',
              'latest_vars' : ('time','lat','lon','z','u','v','wspd', 'wdir'),
             },
    }
