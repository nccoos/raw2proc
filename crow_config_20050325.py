platform_info = {
    'id' : 'crow',
    'location' : 'Crow Branch Creek, Chapel Hill, NC',
    'lat' : 35.942123,  # degrees true (-) south, (+) north
    'lon' : -79.058261, # degrees true (-) west, (+) east
    'mvar' : -8.5,      # degrees (-) west, (+) east
    'altitude': 156.,       # station altitude
    'altitude_units' : 'm',
    'altitude_reference' : 'above_sea_level', 
    # 'mean_water_depth' : -25.17, # meters (-) down, (+) up
    # 'mean_water_depth_time_period' : 'June 2005 - Sept 2005',
    'institution' : 'nccoos',
    # 
    'config_start_date' : '2005-03-01 00:00:00',
    'config_end_date' : '2008-08-30 00:00:00', # None or yyyy-mm-dd HH:MM:SS
    'packages' : ('flow', 'wq'),
    }
sensor_info = {
    'flow' : { 'id' : 'flow',
               'description' : 'Stream Flow and Rain Data',
               'raw_dir' : '/seacoos/data/nccoos/level0/crow/flow/',
               'raw_file_glob' : '*.dat',
               'proc_dir' : '/seacoos/data/nccoos/level1/crow/flow/',
               'process_module' : 'proc_cr10x_flow_v2',
               'utc_offset' : 4,      # hours offset to utc
               'press_offset' : 0./12., # pressure gauge offset to staff gauge
               # 'nbins' : 69,
               # 'bin_size' : 0.5,      # meters
               # 'transducer_ht' : 0.5, # meters above the bottom
               # 'blanking_ht' : 1.6,   # meters above transducer
               },
    'wq' : {'id' : 'wq',
            'description' : 'Water Quality',
            'raw_dir' : '/seacoos/data/nccoos/level0/crow/wq/',
            'raw_file_glob' : '*.dat',
            'proc_dir' : '/seacoos/data/nccoos/level1/crow/wq/',
            'process_module' : 'proc_cr10x_wq_v2',
            'utc_offset' : 4,  # hours offset to utc
                   },
    }
    
