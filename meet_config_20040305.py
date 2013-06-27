platform_info = {
    'id' : 'meet',
    'location' : 'Meeting of the Waters Creek, Chapel Hill, NC',
    'lat' : 35.898559,  # degrees true (-) south, (+) north
    'lon' : -79.034915, # degrees true (-) west, (+) east
    'mvar' : -8.5,      # degrees (-) west, (+) east
    'altitude': 130.,   # (approx.) station altitude
    'altitude_units' : 'm',
    'altitude_reference' : 'above_sea_level', 
    # 'mean_water_depth' : -25.17, # meters (-) down, (+) up
    # 'mean_water_depth_time_period' : 'June 2005 - Sept 2005',
    'institution' : 'nccoos',
    # 
    'config_start_date' : '2004-03-05 09:00:00',
    'config_end_date' : '2004-12-31 00:00:00', # None or yyyy-mm-dd HH:MM:SS
    'packages' : ('flow', 'wq'),
    }
sensor_info = {
    'flow' : { 'id' : 'flow',
               'description' : 'Stream Flow and Rain Data',
               # flow and wq data originially on same sample period so not split
               # during this configuration period so raw flow data in raw wq
               'raw_dir' : '/seacoos/data/nccoos/level0/meet/wq/',
               'raw_file_glob' : 'mow_wq_*',
               'proc_dir' : '/seacoos/data/nccoos/level1/meet/flow',
               'process_module' : 'proc_cr10x_flow_v1',
               'utc_offset' : 4,      # hours offset to utc
               'press_offset' : 0./12., # pressure gauge offset to staff gauge
               # 'nbins' : 69,
               # 'bin_size' : 0.5,      # meters
               # 'transducer_ht' : 0.5, # meters above the bottom
               # 'blanking_ht' : 1.6,   # meters above transducer
               },
    'wq' : {'id' : 'wq',
                   'description' : 'Water Quality',
                   'raw_dir' : '/seacoos/data/nccoos/level0/meet/wq/',
                   'raw_file_glob' : 'mow_wq_*',
                   'proc_dir' : '/seacoos/data/nccoos/level1/meet/wq',
                   'process_module' : 'proc_cr10x_wq_v1',
                   'utc_offset' : 4,  # hours offset to utc
                   },
    }
    
