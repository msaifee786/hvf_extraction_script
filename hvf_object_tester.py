###############################################################################
# hvf_object_tester.py
#
# Description:
#	Tests the HVF_Object class. There are 3 different things this class does:
#
#		- Demos result from a specific HVF file. Usage:
#		  python hvf_object_tester -i <hvf_image_path>
#
#		- Runs unit tests of the (optional) specified collection. If collection
# 		  not specified, defaults to 'default'. Pulls the reference images and
# 		  expected outputs from folder "hvf_test_cases/<collection>").
#		  Usage:
#		  python hvf_object_tester -t [<collection>]
#
#		- Adds a specific HVF image file to unit test case of the specified
# 		  collection. If collection not specified, defaults to 'default'. The
# 		  expected result is generated from the current version of the
# 		  hvf_object, so this should only be used when the current version is
# 		  functional/working, or the resulting output file is corrected.
#		  Usage:
#		  python hvf_object_tester -a <hvf_image_path> [-t <collection>]
#
#
#
###############################################################################

# Import necessary packages
import cv2;
import sys;
import argparse;
import difflib;
from shutil import copyfile
import os
import numpy as np

# Import the HVF_Object class
from hvf_extraction_script.hvf_data.hvf_object import Hvf_Object;

# Import logger class to handle any messages:
from hvf_extraction_script.utilities.logger import Logger;

# Import general file functions:
from hvf_extraction_script.utilities.file_utils import File_Utils;

# Import tester class:
from hvf_extraction_script.hvf_manager.hvf_test import Hvf_Test;

# Default directory for unit tests:
default_unit_test_dir = "default"


# Construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-i", "--image", required=False,
	help="path to input HVF image file to test")
ap.add_argument('-t', '--test', nargs='?', const=default_unit_test_dir)
ap.add_argument("-a", "--add_test_case", required=False,
	help="adds input hvf image to test cases")
args = vars(ap.parse_args())


# Set up the logger module:
#debug_level = Logger.DEBUG_FLAG_INFO;
debug_level = Logger.DEBUG_FLAG_WARNING;
#debug_level = Logger.DEBUG_FLAG_DEBUG;
msg_logger = Logger.get_logger().set_logger_level(debug_level);


###############################################################################
# SINGLE IMAGE TESTING ########################################################
###############################################################################

# If we are passed in an image, read it and show results
if (args["image"]):

	hvf_image = File_Utils.read_image_from_file(args["image"]);
	Hvf_Test.test_single_image(hvf_image);


###############################################################################
# ADD NEW UNIT TESTS ##########################################################
###############################################################################


# If given a new file, add to the unit test to the specified collection. This
# will use the current version of Hvf_Object to generate the expected result
elif (args["add_test_case"]):

	# Load image
	src_path = args["add_test_case"];

	# Load desired test directory to use:
	dir = args["test"];

	if not dir:
		dir = default_unit_test_dir

	if not dir.endswith("/"):
		dir = dir + "/";

	Hvf_Test.add_unit_test(src_path, dir);


###############################################################################
# BULK UNIT TESTING ###########################################################
###############################################################################


# If flag, then do unit tests:
elif (args["test"]):

	if (Logger.get_logger_level() > Logger.DEBUG_FLAG_BROADCAST):
		Logger.get_logger().set_logger_level(Logger.DEBUG_FLAG_BROADCAST);

	# Assume argument is the testing directory. Make sure its in format of directory

	dir = args["test"];

	if not dir.endswith("/"):
		dir = dir + "/";

	Hvf_Test.test_unit_tests(dir);
