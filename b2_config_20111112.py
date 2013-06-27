platform_info = {
 	    'id' : 'b2',
 	    'location' : 'Raleigh Bay, 17 nm South of Ocracoke, NC',
 	    'lat' : 34.7824,   # degrees true (-) south, (+) north
 	    'lon' : -75.9410,  # degrees true (-) west, (+) east
 	    'mvar' : -10.4,    # degrees (-) west, (+) east
            'altitude': 0.,   # (approx.) station altitude
            'altitude_units' : 'm',
            'altitude_reference' : 'sea_surface',
            #
            'mean_water_depth': -29.2, # meters (96 feet)
            'mean_water_depth_time_period': 'Not determined',
 	    'institution' : 'nccoos',
 	    #
 	    'config_start_date' : '2011-11-13 00:00:00',
 	    'config_end_date' : '2012-04-03 20:00:00', # None or yyyy-mm-dd HH:MM:SS
 	    'packages' : ('met', 'wind', 'ctd1', 'ctd2'),
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
 	    }

sensor_info = {
    'met' : { 'id' : 'met',
              'description' : 'Meterological Data from Buoy',
              'raw_dir' : '/seacoos/data/nccoos/level0/b2/met/',
              'raw_file_glob' : '*.dat',
              'proc_dir' : '/seacoos/data/nccoos/level1/b2/met/',
              'process_module' : 'proc_cr1000_met',
              'utc_offset' : 0,  # hours offset to utc of sampling time
              'barometer_height'   : 1.5,   # meters
              'temperature_height' : 1.5,   # meters 
              'height_units' : 'm',
              'height_reference' : 'sea_surface',
              # Recommended
              'source': 'Heise Baro, Rotronics Temp/RH, RM Young Precip, Eppley PSP/PIR',
              # 'latest_dir' : '/seacoos/data/nccoos/latest_v2.0',
              # 'latest_vars' : ('time','lat','lon','z','u', 'v', 'wspd', 'wdir'),
              'plot_module': 'plot_cr1000_met',
              'plot_names': ('timeseries',),
             },
    'wind' : { 'id' : 'wind',
              'description' : 'Wind Data averaged for one minute each sample period',
              'raw_dir' : '/seacoos/data/nccoos/level0/b2/wind/',
              'raw_file_glob' : '*.dat',
              'proc_dir' : '/seacoos/data/nccoos/level1/b2/wind/',
              'process_module' : 'proc_cr1000_wind',
              'utc_offset' : 0,  # hours offset to utc of sampling time
              'anemometer1_height' : 3.66,  # meters (12 ft)
              'anemometer2_height' : 3.35,  # meters (11 ft above sea surface)
              'height_units' : 'm',
              'height_reference' : 'sea_surface',
              # Recommended
              'source': 'RM Young Marine Wind Monitor 5106',
              # 'latest_dir' : '/seacoos/data/nccoos/latest_v2.0',
              # 'latest_vars' : ('time','lat','lon','z','u', 'v', 'wspd', 'wdir'),
              'plot_module': 'plot_cr1000_wind',
              'plot_names': ('timeseries',),
             },
    'ctd1' : { 'id' : 'ctd1',
              'description' : 'Near-surface CTD Data each sample period',
              'raw_dir' : '/seacoos/data/nccoos/level0/b2/ctd1/store/2011_11',
              'raw_file_glob' : '*',
              'proc_dir' : '/seacoos/data/nccoos/level1/b2/ctd1/',
              'process_module' : 'proc_sbe37_ctd',
              'utc_offset' : 0,  # hours offset to utc of sampling time
              'nominal_depth' : -2.0,  # meters 
              'depth_units' : 'm',
              'depth_reference' : 'sea_surface',
              # Recommended
              'source': 'Seabird (SBE) 37 IMP',
              # 'latest_dir' : '/seacoos/data/nccoos/latest_v2.0',
              # 'latest_vars' : ('time','lat','lon','z','depth', 'wtemp', 'cond', 'salin', 'density'),
              'plot_module': 'plot_cr1000_ctd',
              'plot_names': ('timeseries',),
             },
    'ctd2' : { 'id' : 'ctd2',
               'description' : 'Mid-level CTD Data each sample period',
              'raw_dir' : '/seacoos/data/nccoos/level0/b2/ctd2/store/2011_11',
              'raw_file_glob' : '*',
              'proc_dir' : '/seacoos/data/nccoos/level1/b2/ctd2/',
              'process_module' : 'proc_sbe37_ctd',
              'utc_offset' : 0,  # hours offset to utc of sampling time
              'nominal_depth' : -15.0,  # meters 
              'depth_units' : 'm',
              'depth_reference' : 'sea_surface',
              # Recommended
              'source': 'Seabird (SBE) 37 IMP',
              # 'latest_dir' : '/seacoos/data/nccoos/latest_v2.0',
              # 'latest_vars' : ('time','lat','lon','z','depth', 'wtemp', 'cond', 'salin', 'density'),
              'plot_module': 'plot_cr1000_ctd',
              'plot_names': ('timeseries',),
             },
    }
