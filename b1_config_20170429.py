platform_info = {
 	    'id' : 'b1',
 	    'location' : 'Hatteras Bay, 20 nm East of Oregon Inlet, NC',
 	    'lat' : 35.7782,   # degrees true (-) south, (+) north
 	    'lon' : -75.0947,  # degrees true (-) west, (+) east
 	    'mvar' : -11.3,    # degrees (-) west, (+) east
            'altitude': 0.,   # (approx.) station altitude
            'altitude_units' : 'm',
            'altitude_reference' : 'sea_surface',
            #
            'mean_water_depth': -36.0,
            'mean_water_depth_time_period': 'Not determined',
 	    'institution' : 'nccoos',
 	    #
 	    'config_start_date' : '2017-04-29 19:00:00',
 	    'config_end_date' : None, # None or yyyy-mm-dd HH:MM:SS
 	    # 'config_end_date' : '2017-04-01 00:00:00', # None or yyyy-mm-dd HH:MM:SS
 	    'packages' : ('met', 'wind', 'ctd1', 'ctd2', 'comp', 'sys', 'gps'),
            # Required by CF
            'institution' : 'Unversity of North Carolina at Chapel Hill (UNC-CH)',
            'institution_url' : 'http://nccoos.org',
            'institution_dods_url' : 'http://nccoos.org',
            'contact' : 'Sara Haines (haines@email.unc.edu)',
            'conventions' : 'CF-1.0; SEACOOS-CDL-v2.0',
            # Required by Scout
            'format_category_code' : 'fixed-point',
            'institution_code' : 'nccoos',
            # Recommended
            'project' : 'North Carolina Coastal Ocean Observing System (NCCOOS)',
            'project_url' : 'http://nccoos.org',            
            'metadata_url' : 'http://nccoos.org',
            'references' : 'http://nccoos.org',
            'source': 'Buoy CR1000 Datalogger',
            # Needed for processing NDBC output
            'ndbc_module' : 'ndbc_41062',
            'ndbc_id': '41062',
            'ndbc_dir' : '/seacoos/data/nccoos/latest_ndbc',
            'ndbc_missing' : -9999.0,
            # report data to NDBC closest to top of each hour +/- 6 min
            'ndbc_sample_interval':(1,'hour'),
            'ndbc_sample_offset':(0,'minute'),
            'ndbc_time_tolerance':(30,'minute'),
            # report data closest to 0:10 and 0:40 each hour +/- 3 min
            # 'ndbc_sample_interval':(30,'minute'), # every 30 min
            # 'ndbc_sample_offset':(10,'minute'), # offset by +10 min
            # 'ndbc_time_tolerance':(3,'minute'),
 	    }

sensor_info = {
    'met' : { 'id' : 'met',
              'description' : 'Meterological Data averaged for one minute each sample period',
              'raw_dir' : '/seacoos/data/nccoos/level0/b1/met/',
              'raw_file_glob' : '*.dat',
              'proc_dir' : '/seacoos/data/nccoos/level1/b1/met/',
              'process_module' : 'proc_cr1000_met',
              'utc_offset' : 0,  # hours offset to utc of sampling time
              'barometer_height'   : 1.5,   # meters
              'temperature_height' : 1.5,   # meters 
              'height_units' : 'm',
              'height_reference' : 'sea_surface',
              'source': 'Heise Baro, Rotronics Temp/RH, RM Young Precip, Eppley PSP/PIR',
              # 'latest_dir' : '/seacoos/data/nccoos/latest_v2.0',
              # 'latest_vars' : ('time','lat','lon','z','atemp', 'baro', 'rh', 'rain', 'psp', 'pir'),
              'ndbc_vars' : ('air_temp', 'air_press', 'rh', 'psp', 'pir'),
              'ndbc_tags' : ('atmp1', 'baro1', 'rrh', 'srad1', 'lwrad'),
              'ndbc_units' : ('degC', 'hPa', '%', 'W m-2', 'W m-2'),
              'plot_module': 'plot_cr1000_met',
              'plot_names': ('timeseries',),
             },
    'wind' : { 'id' : 'wind',
              'description' : 'Wind Data averaged for one minute each sample period',
              'raw_dir' : '/seacoos/data/nccoos/level0/b1/wind/',
              'raw_file_glob' : '*.dat',
              'proc_dir' : '/seacoos/data/nccoos/level1/b1/wind/',
              'process_module' : 'proc_cr1000_wind',
              'utc_offset' : 0,  # hours offset to utc of sampling time
              'anemometer1_height' : 3.66,  # meters (12 ft)
              'anemometer2_height' : 3.35,  # meters (11 ft above sea surface)
              'height_units' : 'm',
              'height_reference' : 'sea_surface',
               # Required offset corrections wdir1-wdir2 = -90
               # wdir1 looks okay for this time period from other nearest neighbors
               # 2017-04-29 19:00:00 until current time 
               'offset_vars' : ('wdir2',),
               'offset_vals' : (-90.0,),
              # Recommended
              'source': 'RM Young Marine Wind Monitor 5106',
               # 'latest_dir' : '/seacoos/data/nccoos/latest_v2.0',
              # 'latest_vars' : ('time','lat','lon','z','u', 'v', 'wspd', 'wdir'),
              'ndbc_vars' : ('wspd1', 'wdir1', 'wgust1', 'wspd2', 'wdir2', 'wgust2'),
              'ndbc_tags' : ('wspd1', 'wdir1', 'gust1', 'wspd2', 'wdir2', 'gust2'),
              'ndbc_units' : ('m s-1', 'degrees', 'm s-1', 'm s-1', 'degrees', 'm s-1'),
              'plot_module': 'plot_cr1000_wind',
              'plot_names': ('timeseries',),
             },
    'ctd1' : { 'id' : 'ctd1',
              'description' : 'Near-surface CTD Data each sample period',
              'raw_dir' : '/seacoos/data/nccoos/level0/b1/ctd1/',
              'raw_file_glob' : '*',
              'proc_dir' : '/seacoos/data/nccoos/level1/b1/ctd1/',
              'process_module' : 'proc_cr1000_ctd_v2',
              'utc_offset' : 0,  # hours offset to utc of sampling time
              'nominal_depth' : -2.0,  # meters 
              'depth_units' : 'm',
              'depth_reference' : 'sea_surface',
              # Recommended
              'source': 'Seabird (SBE) 37 IMP',
              # 'latest_dir' : '/seacoos/data/nccoos/latest_v2.0',
              # 'latest_vars' : ('time','lat','lon','z','depth', 'wtemp', 'cond', 'salin', 'density'),
              'ndbc_vars' : ('wtemp','depth', 'wtemp', 'salin'),
              # wtemp recorded in two fields for ndbc
              # wtmp1 tag needed to get into weather obs, others for temp/salin obs
              'ndbc_tags' : ('wtmp1', 'dp001', 'tp001', 'sp001'), 
              'ndbc_units' : ('degC', 'm', 'degC', 'psu'), 
              'plot_module': 'plot_cr1000_ctd',
              'plot_names': ('timeseries',),
             },
    'ctd2' : { 'id' : 'ctd2',
               'description' : 'Mid-level CTD Data each sample period',
              'raw_dir' : '/seacoos/data/nccoos/level0/b1/ctd2/',
              'raw_file_glob' : '*',
              'proc_dir' : '/seacoos/data/nccoos/level1/b1/ctd2/',
              'process_module' : 'proc_cr1000_ctd_v2',
              'utc_offset' : 0,  # hours offset to utc of sampling time
              'nominal_depth' : -15.0,  # meters 
              'depth_units' : 'm',
              'depth_reference' : 'sea_surface',
              # Recommended
              'source': 'Seabird (SBE) 37 IMP',
              # 'latest_dir' : '/seacoos/data/nccoos/latest_v2.0',
              # 'latest_vars' : ('time','lat','lon','z','depth', 'wtemp', 'cond', 'salin', 'density'),
              'ndbc_vars' : ('depth', 'wtemp', 'salin'),
              'ndbc_tags' : ('dp002', 'tp002', 'sp002'),
              'ndbc_units' : ('m', 'degC', 'psu'), 
              'plot_module': 'plot_cr1000_ctd',
              'plot_names': ('timeseries',),
             },
    'comp' : { 'id' : 'comp',
              'description' : 'Compass data averaged for one minute each sample period',
              'raw_dir' : '/seacoos/data/nccoos/level0/b1/comp/',
              'raw_file_glob' : '*.dat',
              'proc_dir' : '/seacoos/data/nccoos/level1/b1/comp/',
              'process_module' : 'proc_cr1000_comp',
              'utc_offset' : 0,  # hours offset to utc of sampling time
              'compass_height'   : 1.5,   # meters
              'height_units' : 'm',
              'height_reference' : 'sea_surface',
              'source': 'Honeywell Digital Compass',
              'plot_module': 'plot_cr1000_comp',
              'plot_names': ('timeseries',),
             },
    'sys' : { 'id' : 'sys',
              'description' : 'CR1000 System Data',
              'raw_dir' : '/seacoos/data/nccoos/level0/b1/sys/',
              'raw_file_glob' : '*.dat',
              'proc_dir' : '/seacoos/data/nccoos/level1/b1/sys/',
              'process_module' : 'proc_cr1000_sys',
              'utc_offset' : 0,  # hours offset to utc of sampling time
              'canister_height'   : 1.5,   # meters
              'height_units' : 'm',
              'height_reference' : 'sea_surface',
              'source': 'CR1000 batt, canister temp, and leak detect',
              'plot_module': 'plot_cr1000_sys',
              'plot_names': ('timeseries',),
             },
    'gps' : { 'id' : 'gps',
              'description' : 'CR1000 GPS Data',
              'raw_dir' : '/seacoos/data/nccoos/level0/b1/gps/',
              'raw_file_glob' : '*.dat',
              'proc_dir' : '/seacoos/data/nccoos/level1/b1/gps/',
              'process_module' : 'proc_cr1000_gps',
              'utc_offset' : 0,  # hours offset to utc of sampling time
              'source': 'Garmin HVS 19x GPS ',
              'plot_module': 'plot_cr1000_gps',
              'plot_names': ('watch_circle',),
             },
    }
