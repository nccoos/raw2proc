#!/usr/bin/env python
# Last modified:  Time-stamp: <2011-05-11 15:59:31 haines>
"""
Quality Control Tests and Utilities
"""

def range_test(val, lower_limit, upper_limit):
    """ QC Range Test

      Test whether value is inclusively within established upper and lower limit
    
      :Parameters:
       val : scalar, list, or numpy.array
         value(s) to be tested
       lower_limit : scalar
         Any value less than lower limit fails
       upper_limit : scalar
         Any value more than upper limit fails

      :Returns:
         flag : boolean, list, numpy.array
         True = Pass
         False = Fail
      
    """
    flag = (val > lower_limit) & (val < upper_limit)
    return (flag)

def time_continuity_test(val, factor, v1, v2, t1, t2):
    """ QC Time-Continuity Test

    Checks the amount of change in each measurment's value over the
    given time period. If same or less than empirical form or constant
    maximum of allowable change for a given time difference, then the
    test passes.
    
    """
    flag = abs((v2-v1)/(t2-t1)) <= factor
    return (flag)

# **** pack and unpack go in ncutil.py
def nc_pack_qcflags(qcflag, rtype='int8'):
    """ Pack boolean numpy.array and cast for netcdf
    padding where necessary
    """
    # check if boolean

    # convert bool to int (0,1)
    q1=qcflag.astype(int)
    # pack 1s and 0s into a uint8 array
    # (other dtype in this step not optional with numpy.packbits)
    q2=numpy.packbits(q1,axis=1)
    # cast uint8 to int8 (NC_BYTE)
    qcflag=numpy.cast['int8'](q2)

    return (qcflag)

def nc_unpack_qcflags(qcflag):
    """
    """

    # check if uint8 (?)

    # cast int8 (NC_BYTE) to uint8
    q1=numpy.cast['uint8'](qcflag)
    # unpack uint8 to 1s and 0s
    q2=numpy.unpackbits(q1, axis=1)
    #
    qcflags=q2.astype(bool)
