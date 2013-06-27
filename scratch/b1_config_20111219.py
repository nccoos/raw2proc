platform_info = {
 	    'id' : 'b1',
 	    'location' : 'Hatteras Bay, 20 nm East of Oregon Inlet, NC',
 	    'lat' : 35.7885,   # degrees true (-) south, (+) north
 	    'lon' : -75.1053,  # degrees true (-) west, (+) east
 	    'mvar' : -11.3,    # degrees (-) west, (+) east
            'altitude': 0.,   # (approx.) station altitude
            'altitude_units' : 'm',
            'altitude_reference' : 'sea_surface',
            #
            'mean_water_depth': -32.0,
            'mean_water_depth_time_period': 'Not determined',
 	    'institution' : 'nccoos',
 	    #
 	    'config_start_date' : '2011-12-19 00:00:01',
 	    'config_end_date' : '2012-04-06 00:00:00', # None or yyyy-mm-dd HH:MM:SS
 	    'packages' : ('ctd1', 'ctd2'),
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
    'ctd1' : { 'id' : 'ctd1',
              'description' : 'Near-surface CTD Data each sample period',
              'raw_dir' : 'http://whewell.marine.unc.edu/data/nccoos/level0/b1/ctd1/store/2011_11',
              'raw_file_glob' : '*',
              'proc_dir' : '/seacoos/data/nccoos/level1/b1/ctd1/',
              'process_module' : 'proc_sbe37_ctd',
              'utc_offset' : 0,  # hours offset to utc of sampling time
              'nominal_depth' : -2.0,  # meters 
              'depth_units' : 'm',
              'depth_reference' : 'sea_surface',
              # 'latest_dir' : '/seacoos/data/nccoos/latest_v2.0',
              # 'latest_vars' : ('time','lat','lon','z','depth', 'wtemp', 'cond', 'salin', 'density'),
              # Recommended
              'source': 'Seabird (SBE) 37 IMP',
             },
    'ctd2' : { 'id' : 'ctd2',
               'description' : 'Mid-level CTD Data each sample period',
              'raw_dir' : '/seacoos/data/nccoos/level0/b1/ctd2/store/2011_11',
              'raw_file_glob' : '*',
              'proc_dir' : '/seacoos/data/nccoos/level1/b1/ctd2/',
              'process_module' : 'proc_sbe37_ctd',
              'utc_offset' : 0,  # hours offset to utc of sampling time
              'nominal_depth' : -15.0,  # meters 
              'depth_units' : 'm',
              'depth_reference' : 'sea_surface',
              # 'latest_dir' : '/seacoos/data/nccoos/latest_v2.0',
              # 'latest_vars' : ('time','lat','lon','z','depth', 'wtemp', 'cond', 'salin', 'density'),
              # Recommended
              'source': 'Seabird (SBE) 37 IMP',
             },
    }
