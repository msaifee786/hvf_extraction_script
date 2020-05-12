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
ap.add_argument("-d", "--dicom", required=False,
	help="path to input DICOM file to test")
ap.add_argument('-t', '--test', nargs='?', const=default_unit_test_dir)
ap.add_argument("-a", "--add_test_case", required=False,
	help="adds input hvf image to test cases")
ap.add_argument("-s", "--test_serialized_data", required=False,
	help="test serialized data")
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
# DICOM FILE TESTING ##########################################################
###############################################################################
if (args["dicom"]):

	hvf_dicom = File_Utils.read_dicom_from_file(args["dicom"]);
	hvf_obj = Hvf_Object.get_hvf_object_from_dicom(hvf_dicom);
	print(hvf_obj.get_pretty_string());


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

###############################################################################
# SERIALIZED DATA TESTING ###########################################################
###############################################################################
# If flag, then do unit tests:
elif (args["test_serialized_data"]):

	if (Logger.get_logger_level() > Logger.DEBUG_FLAG_BROADCAST):
		Logger.get_logger().set_logger_level(Logger.DEBUG_FLAG_BROADCAST);

	# Assume argument is the testing directory. Make sure its in format of directory

	dir = os.path.join("hvf_serialized_tests", args["test_serialized_data"]);

	reference_data_dir = os.path.join(dir, "reference_data");
	test_data_dir = os.path.join(dir, "test_data");

	testing_data_list = []

	for hvf_text_file in os.listdir(reference_data_dir):

		# Skip hidden files:
		if hvf_text_file.startswith('.'):
			continue;

		# Then, find corresponding serialization text file
		filename_root, ext = os.path.splitext(hvf_text_file);

		# Load data into hvf_obj. Assume same file name
		reference_file_path = os.path.join(reference_data_dir, hvf_text_file)
		reference_data_text = File_Utils.read_text_from_file(reference_file_path);
		reference_hvf_obj = Hvf_Object.get_hvf_object_from_text(reference_data_text);


		test_file_path = os.path.join(test_data_dir, hvf_text_file)
		test_data_text = File_Utils.read_text_from_file(test_file_path);
		test_hvf_obj = Hvf_Object.get_hvf_object_from_text(test_data_text);

		testing_data_dict, testing_msgs = Hvf_Test.test_hvf_obj(filename_root, reference_hvf_obj, test_hvf_obj)
		testing_data_dict["time"] = 0;

		# Print messages
		for msg in testing_msgs:
			Logger.get_logger().log_msg(debug_level, msg)


		testing_data_list.append(testing_data_dict);

	Hvf_Test.print_unit_test_aggregate_metrics(testing_data_list);
