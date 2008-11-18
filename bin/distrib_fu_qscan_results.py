#!/usr/bin/env python
"""
$Id$

Manager program to run specific parts of the followup on the CCIN2P3 cluster
"""

__author__ = 'Romain Gouaty  <gouaty@lapp.in2p3.fr>'
__date__ = '$Date$'
__version__ = '$Revision$'[11:-2]

##############################################################################
# import standard modules

import sys
import tarfile
import os, shutil
from subprocess import *
import copy
import re
import exceptions
import glob
import fileinput
import linecache
import string
from optparse import *
from types import *
import operator
from UserDict import UserDict
sys.path.append('@PYTHONLIBDIR@')

##############################################################################
# import the modules we need from GLUE/LAL/LALAPPS/PYLAL

from pylal import fu_utils

##############################################################################
#
#  MAIN PROGRAM
#
##############################################################################

######################## OPTION PARSING  #####################################

usage = """
usage: %prog [options]
"""
parser = OptionParser( usage )


parser.add_option("-v","--version",action="store_true",default=False,\
    help="display version information and exit")

parser.add_option("-i","--qscan-input-file",action="store",type="string",\
    help="input file containing the qscan results. It must be a tar.gz file")

parser.add_option("","--qscan-cache-background",action="store",type="string", \
    help="qscan cache file for background")

parser.add_option("","--qscan-cache-foreground",action="store",type="string", \
    help="qscan cache file for foreground")

parser.add_option("","--remote-ifo",action="store",type="string",\
    help="name of the interferometer for which the qscans were performed \
    remotely (example: V1)")

parser.add_option("","--qscan-type-list",action="store",type="string",\
    help="types of qscan to be analysed (example: \"foreground-qscan,foreground-seismic-qscan,background-qscan,background-seismic-qscan\")")

nd_line = sys.argv[1:]
(opts,args) = parser.parse_args()

#################################
# if --version flagged
if opts.version:
  print "$Id$"
  sys.exit(0)

#################################
# Sanity check of input arguments

if not opts.qscan_input_file:
  print >> sys.stderr, "No input file specified!!"
  print >> sys.stderr, "Use --qscan-input-file FILE to specify location."
  sys.exit(1)

if not opts.qscan_cache_background:
  print >> sys.stderr, "No cache file specified for qscan background!!"
  print >> sys.stderr, "Use --qscan-cache-background FILE to specify location."
  sys.exit(1)

if not opts.qscan_cache_foreground:
  print >> sys.stderr, "No cache file specified for qscan foreground!!"
  print >> sys.stderr, "Use --qscan-cache-foreground FILE to specify location."
  sys.exit(1)

if not opts.remote_ifo:
  print >> sys.stderr, "No ifo specified!!"
  print >> sys.stderr, "Use --remote-ifo to specify the interferometer (example \"V1\")."
  sys.exit(1)

if not opts.qscan_type_list:
  print >> sys.stderr, "No qscan type specified!!"
  print >> sys.stderr, "Use --qscan-type-list to specify the list of types (example \"foreground-qscan,foreground-seismic-qscan,background-qscan,background-seismic-qscan\")."
  sys.exit(1)


#################################
# CORE OF THE PROGRAM

qscanTypeList = [qscanType.strip() for qscanType in opts.qscan_type_list.split(",")]

# get the list of qscans in the cache files
if os.path.exists(opts.qscan_cache_foreground) and os.path.exists(opts.qscan_cache_background):
  for qscan_type in qscanTypeList:
    exec(qscan_type.replace('-','_') + "List = fu_utils.getPathFromCache(opts.qscan_cache_" + qscan_type.split('-')[0] + ",qscan_type,opts.remote_ifo)")
else:
  print >> sys.stderr, "File " + opts.qscan_cache_foreground + " or " + opts.qscan_cache_background+ " could not be found!!"
  sys.exit(1)


# Check for the existence of the qscan-input-file and try to uncompress it
if os.path.exists(opts.qscan_input_file):
  if tarfile.is_tarfile(opts.qscan_input_file):
    tar = tarfile.open(opts.qscan_input_file,"r:gz")
    file_list = tar.getnames()
    for file in file_list:
      tar.extract(file)
    tar.close()
  else:
    print >> sys.stderr, "File " + opts.qscan_input_file + " is not a valid tar file!!"
    sys.exit(1)
else:
  print >> sys.stderr, "File " + opts.qscan_input_file + " could not be found!!"
  sys.exit(1)


for qscan_type in qscanTypeList:
  for qscan in eval(qscan_type.replace('-','_') + "List"):
    # define the input path of the qscan directory to be copied
    qscan_result_path = opts.qscan_input_file.strip(".tar.gz")+ "/RESULTS/results_" + qscan_type + "/" + qscan[1]
    # check if directory exists before trying to move it
    if os.path.exists(qscan_result_path):
      # do not overwrite an existing output directory
      if os.path.exists(qscan[0]):
        print >> sys.stderr, "Directory " + qscan[0] + " already exists, cannot be overwritten with new qscan results"
      else:
        shutil.move(qscan_result_path, qscan[0]) 
        print "\n Copying file " + qscan_result_path + " to " + qscan[0]
    else:
      print >> sys.stderr, "Directory " + qscan_result_path + " could not be found!!"
      sys.exit(1)


# Do some cleaning in the local directory before exiting
if os.path.exists(opts.remote_ifo + "_qscans_results"):
  shutil.rmtree(opts.remote_ifo + "_qscans_results")

