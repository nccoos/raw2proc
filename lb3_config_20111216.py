platform_info = {
 	    'id' : 'lb3',
 	    'location' : 'Long Bay, NC, Upper Slope Bottom Frame',
 	    'lat' : 32.85237,   # degrees true (-) south, (+) north
 	    'lon' : -78.01322,  # degrees true (-) west, (+) east
 	    'mvar' : -8.9,    # degrees (-) west, (+) east
            'altitude': 0.,   # (approx.) station altitude
            'altitude_units' : 'm',
            'altitude_reference' : 'sea_surface',
            #
            'mean_water_depth': -176.0,
            'mean_water_depth_time_period': 'Not determined',
 	    'institution' : 'nccoos',
 	    #
 	    'config_start_date' : '2011-12-16 00:00:00',
 	    'config_end_date' : '2012-04-03 15:45:00', # None or yyyy-mm-dd HH:MM:SS
 	    'packages' : ('ctd', ),
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
            'project' : 'Long Bay (LB) Wintertime Blooms',
            'project_url' : 'http://nccoos.org/projects/long-bay-wintertime-blooms',            
            'metadata_url' : 'http://nccoos.org',
            'references' : 'http://nccoos.org',
            'source': 'SKIO Bottom Frame',
 	    }

sensor_info = {
    'ctd' : { 'id' : 'ctd',
              'description' : 'Bottom CTD Data each sample period',
              'raw_dir' : '/seacoos/data/long_bay/level0/lb3/ctd/2011_12/',
              'raw_file_glob' : '*',
              'proc_dir' : '/seacoos/data/long_bay/level1/lb3/ctd/',
              'process_module' : 'proc_sbe37_ctd',
              'utc_offset' : 0,  # hours offset to utc of sampling time
              'nominal_depth' : -175.0,  # meters 
              'depth_units' : 'm',
              'depth_reference' : 'sea_surface',
              # Recommended
              'source': 'Seabird (SBE) 37 SM',
              # 'latest_dir' : '/seacoos/data/nccoos/latest_v2.0',
              # 'latest_vars' : ('time','lat','lon','z','depth', 'wtemp', 'cond', 'salin', 'density'),
              'plot_module': 'plot_cr1000_ctd',
              'plot_names': ('timeseries',),
             },
    }
