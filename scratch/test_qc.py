#!/usr/bin/env /opt/env/haines/dataproc/bin/python
# Last modified:  Time-stamp: <2011-05-05 15:06:38 haines>
"""test_qc"""

import sys
sys.path.append('/opt/env/haines/dataproc/raw2proc')
from ncutil import *
from pycdf import *

import numpy

wtemp = numpy.array([1.1, 1.2, 1.3, -9999, 1.3, 1.2, 1.1, 5, 1.0, 1.0, 0.9, 1.2, 1.5, 1.7, 2., 2., 1.9, 80])
time = numpy.arange(wtemp.size)

# set print options to suppress the scientific notation
numpy.set_printoptions(suppress=True)
print wtemp
qc = (wtemp>-50) & (wtemp<50)
print qc
print qc.astype(int)

q3=numpy.zeros((18,8), dtype=int)

# fill from LSB to MSB (big-endian)
# .astype(int) method converts to bool to int (1s and 0s)
q3[:,-1]=qc.astype(int)
q3[:,-2]=qc.astype(int)

# pack 1s and 0s into a uint8 array
# numpy.packbits on converts to uint8
# (no other data type is available
# with numpy.packbits), 
q4=numpy.packbits(q3,axis=1)
q5 = numpy.squeeze(q4)
print q5
print q5.shape

global_atts = {'title' : 'test_qc.nc'}
var_atts = {
    'time' : {'short_name' : 'time',
              'units': '',
              },
    'wtemp' : {'short_name' : 'wtemp',
               'standard_name' : 'water_temperature', 
               'units': 'degrees_C',
               'ancillary_variables' : 'wtemp_qc',
               },
    'wtemp_qc' : {'short_name' : 'wtemp_qc',
                  'standard_name' : 'water_temperature quality_flag',
                  '_FillValue' : 0,
                  'valid_range' : (0,255),
                  'flag_masks' : (1,2,4,8),
                  'flag_meanings' : 'sensor_health_ok within_sensor_range within_gross_range below_time_continuity',
                  'sensor_range' : (-5, 45),
                  'gross_range' : (-5, 40),
                  'time_continuity_factor' : 8.6,
                  },
    }
dim_inits = (
    ('ntime', NC.UNLIMITED),
    )
var_inits = (
    ('time', NC.INT, ('ntime',)),
    ('wtemp', NC.FLOAT, ('ntime',)),
    ('wtemp_qc', NC.BYTE, ('ntime',)),
    )
var_data = (
    ('time', time),
    ('wtemp', wtemp),
    ('wtemp_qc', q5),
    )

nc_create('./test_qc.nc', (global_atts, var_atts, dim_inits, var_inits, var_data))

#############################################################

# use valid_range to indicate uint8 for NC_BYTE
# to set 5-bit (LSB)
# flag_masks = 1b, 2b, 4b, 8b, 16b
# be sure to set valid_range 
# valid_range = 1b, 31b

# According to CF Metadata and NUG, this is how we should treat uint8
# byte data in netcdf:
#
# "The netCDF data types char, byte, short, int, float or real, and
# double are all acceptable. The char type is not intended for numeric
# data. One byte numeric data should be stored using the byte data
# type. All integer types are treated by the netCDF interface as
# signed. It is possible to treat the byte type as unsigned by using
# the NUG convention of indicating the unsigned range using the
# valid_min, valid_max, or valid_range attributes."
# (Section 2.2 Data Types in  "CF Metadata CF Conventions 1.4"
# http://cf-pcmdi.llnl.gov/documents/cf-conventions/1.4/ch02s02.html)

# netcdf types
# NC_BYTE 8-bit signed integer (int8)
# NC_CHAR 8-bit unsigned integer (uint8)
# NC_SHORT 16-bit signed integer (int16)
# NC_INT and NC_LONG 32-bit signed integer (int32)
# NC_FLOAT 32-bit float (float32)
# NC_DOUBLE 64-bit float (float64)

