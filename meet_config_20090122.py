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
    'config_start_date' : '2009-01-01 00:00:00',
    'config_end_date' : '2012-06-01', # None or yyyy-mm-dd HH:MM:SS
    'packages' : ('flow', 'wq'),
    }
sensor_info = {
    'flow' : { 'id' : 'flow',
               'description' : 'Stream Flow and Rain Data',
               'raw_dir' : '/seacoos/data/nccoos/level0/meet/flow/',
               'raw_file_glob' : 'mow_flow_*',
               'proc_dir' : '/seacoos/data/nccoos/level1/meet/flow',
               'process_module' : 'proc_cr1000_flow',
               'utc_offset' : 4,      # hours offset to utc
               'press_offset' : 0./12., # pressure gauge offset to staff gauge
               'plot_module' : 'plot_cr1000_flow', 
               'plot_names' : ('timeseries',), 
               'csv_dir' : '/seacoos/data/nccoos/latest_csv',
               'csv_vars' : ('time', 'rain','press_flow','press_wl'),
               },
    'wq' : {'id' : 'wq',
            'description' : 'Water Quality',
            'raw_dir' : '/seacoos/data/nccoos/level0/meet/wq/',
            'raw_file_glob' : 'mow_wq_*',
            'proc_dir' : '/seacoos/data/nccoos/level1/meet/wq',
            'process_module' : 'proc_cr1000_wq',
            'utc_offset' : 4,  # hours offset to utc
            'plot_module' : 'plot_cr1000_wq', 
            'plot_names' : ('timeseries',), 
            'csv_dir' : '/seacoos/data/nccoos/latest_csv',
            'csv_vars' : ('time', 'wtemp','cond','do_sat', 'do_mg', 'ph', 'turb', 'battvolts'),
            },
    }
    
