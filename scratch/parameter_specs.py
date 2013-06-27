template = {
    'param' : {
       'min' : None,
       'max' : None,
       'accuracy' : None,
       'resolution' : None,
       'units' : None,
       'units_reference': None,
       },
    }

parameters = {
    'wind_direction' : {
       'min' : 0.,
       'max' : 360.,
       'accuracy' : 10.0,
       'resolution' : 1.0,
       'units' : 'degrees',
       'units_reference': 'clockwise_from_True_North',
       },
    'wind_speed' : {
       'min' : 0.,
       'max' : 62.,
       'accuracy' : 1.0,
       'resolution' : 0.1,
       'units' : 'm s-1',
       'units_reference': None,
       },
    'wind_gust' : {
       'min' : 0.,
       'max' : 82.,
       'accuracy' : 1.0,
       'resolution' : 0.1,
       'units' : 'm s-1',
       'units_reference': None,
       },

    'air_pressure' : {
       'min' : 800.,
       'max' : 1200.,
       'accuracy' : 1.0,
       'resolution' : 0.1,
       'units' : 'hPa',
       'units_reference': None,
       },
    'precipitation_rate' : {
       'min' : 0.,
       'max' : 100.,
       'accuracy' : 5.0,
       'resolution' : 1.0,
       'units' : 'mm hr-1',
       'units_reference': None,
       },

    'air_temperature' : {
       'min' : -50.0,
       'max' : 40.0,
       'accuracy' : 1.0,
       'resolution' : 0.1,
       'units' : 'degrees_celsius',
       'units_reference': None,
       },

    'relative_humidity' : {},
    'dew_point_temperature' : {},
    
    'wave_from_direction' : {
       'min' : 0.,
       'max' : 360.,
       'accuracy' : 10.,
       'resolution' : 0.1,
       'units' : 'degrees',
       'units_reference': 'clockwise_from_True_North',
       },
    'wave_height' : {
       'min' : 0.,
       'max' : 35.,
       'accuracy' : 0.2,
       'resolution' : 0.1,
       'units' : 'm',
       'units_reference': None,
       },
    'wave_period' : {
       'min' : 0.,
       'max' : 30.,
       'accuracy' : 1.,
       'resolution' : 1.,
       'units' : 'second',
       'units_reference': None,
       },

    'water_temperature' : {
       'min' : -5.0,
       'max' : 40.0,
       'accuracy' : 1.0,
       'resolution' : 0.1,
       'units' : 'degrees_celsius',
       'units_reference': None,
       },
    'water_pressure' : {},
    'water_level' : {},

    '' : {},
    '' : {},

    'conductivity' : {},
    'salinity' : {},
    'turbidity' : {},
    'dissolved_oxygen' : {},
    
    }
