#!/usr/bin/env /opt/env/haines/dataproc/bin/python
# Last modified:  Time-stamp: <2011-05-06 12:34:09 haines>
"""test_qc_flags -- bit-valued  flagging system in numpy and for writing out to netcdf"""

import numpy
wtemp = numpy.array([1.1, 1.2, 1.3, -9999, 1.3, 1.2, 1.1, 5, 1.0, 1.0, 0.9, 1.2, 1.5, 1.7, 2., 2., 1.9, 80])

# set print options to suppress the scientific notation
numpy.set_printoptions(suppress=True)
wtemp

# qc = wtemp > -50 and wtemp<50
# this does not work
# one alternative
# qc1 = wtemp>-50
# qc2 = wtemp<50
# qc=numpy.bitwise_and(qc1, qc2)

# but better alternateive (numpy tutorial)
qc = (wtemp>-50) & (wtemp<50)
print qc
# [ True  True  True False  True  True  True  True  True  True  True  True
#   True  True  True  True  True False]
print qc.dtype
# bool
print qc.astype(int)
# [1 1 1 0 1 1 1 1 1 1 1 1 1 1 1 1 1 0]

q3=numpy.zeros((18,8), dtype=int)

# fill from LSB to MSB (big-endian)
# .astype(int) method converts to bool to int (1s and 0s)
q3[:,-1]=qc.astype(int)
q3[:,-2]=qc.astype(int)

# pack 1s and 0s into a uint8 array (other dtype in this step not
# optional with numpy.packbits), 
q4=numpy.packbits(q3,axis=1)

# another option for packing into binary is struct.pack where format can be specified
# in addition to big- and little-endian (if necessary)

print q4
print q4.shape

# squeeze array back to same shape as data
q5 = numpy.squeeze(q4)
print q5
print q5.shape

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


###############################################################
# create columns of test flags (one column for each test)
q1=numpy.row_stack(qc)
q2=numpy.row_stack(qc)
# concatenate columns (axis=1) left to right
q3=numpy.concatenate((q1, q2), axis=1)

# **********  ???? *************
# but this fills the MSB first
# do we really want that?
# should the first test fill the LSB???

# pack 1s and 0s into a uint8 array (other dtype in this step not
# optional with numpy.packbits)
q4=numpy.packbits(q3.astype(int),axis=1)

# another option for packing into binary is struct.pack where format can be specified
# in addition to big- and little-endian (if necessary)

# to store as NC_BYTE cast uint8 to int8
q5=numpy.cast['int8'](q4)

# >>> q3                            >>> q4                        >>> q5                           
# array([[ True,  True],            array([[192],                 array([[-64],                    
#               [ True,  True],                   [192],                        [-64],             
#               [ True,  True],                   [192],                        [-64],             
#               [False, False],                   [  0],                        [  0],             
#               [ True,  True],                   [192],                        [-64],             
#               [ True,  True],                   [192],                        [-64],             
#               [ True,  True],                   [192],                        [-64],             
#               [ True,  True],                   [192],                        [-64],             
#               [ True,  True],                   [192],                        [-64],             
#               [ True,  True],                   [192],                        [-64],             
#               [ True,  True],                   [192],                        [-64],             
#               [ True,  True],                   [192],                        [-64],             
#               [ True,  True],                   [192],                        [-64],             
#               [ True,  True],                   [192],                        [-64],             
#               [ True,  True],                   [192],                        [-64],             
#               [ True,  True],                   [192],                        [-64],             
#               [ True,  True],                   [192],                        [-64],             
#               [False, False]],                  [  0]],                       [  0]], 
#                   dtype=bool)                   dtype=uint8)                  dtype=int8)
#                                   uint8 binary 192 = 1100 0000

# cast back to unsigned 8-bit integer
q6=numpy.cast['uint8'](q5)      # should == q4
q7=numpy.unpackbits(q6, axis=1) # should == q3.astype(int)

# 
print wtemp * q7[0:,1]

# >>> q7
#        array([[1, 1, 0, 0, 0, 0, 0, 0],
#               [1, 1, 0, 0, 0, 0, 0, 0],
#               [1, 1, 0, 0, 0, 0, 0, 0],
#               [0, 0, 0, 0, 0, 0, 0, 0],
#               [1, 1, 0, 0, 0, 0, 0, 0],
#               [1, 1, 0, 0, 0, 0, 0, 0],
#               [1, 1, 0, 0, 0, 0, 0, 0],
#               [1, 1, 0, 0, 0, 0, 0, 0],
#               [1, 1, 0, 0, 0, 0, 0, 0],
#               [1, 1, 0, 0, 0, 0, 0, 0],
#               [1, 1, 0, 0, 0, 0, 0, 0],
#               [1, 1, 0, 0, 0, 0, 0, 0],
#               [1, 1, 0, 0, 0, 0, 0, 0],
#               [1, 1, 0, 0, 0, 0, 0, 0],
#               [1, 1, 0, 0, 0, 0, 0, 0],
#               [1, 1, 0, 0, 0, 0, 0, 0],
#               [1, 1, 0, 0, 0, 0, 0, 0],
#               [0, 0, 0, 0, 0, 0, 0, 0]], dtype=uint8)
