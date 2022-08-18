###############################################################################
# hvf_object_tester.py
#
# Description:
# 	Tests the HVF_Object class. There are 3 different things this class does:
#
# 		- Demos result from a specific HVF file. Usage:
# 		  python hvf_object_tester -i <hvf_image_path>
#
# 		- Runs unit tests of the specified collection. Specify 2 arguments:
# 			- Test name
# 			- Test type (image_vs_serialization, image_vs_dicom, etc -- see Hvf_Test)
# 		  Usage:
# 		  python hvf_object_tester -t <test_name> <test_type>
#
# 		- Adds a unit test to the specified collection/test type. Takes in 4 arguments,
# 		  and copies files into the hvf_test_cases folder
# 		  Usage:
# 		  python hvf_object_tester -a <test_name> <test_type> <ref_data_path> <test_data_path>
#
###############################################################################

# Import necessary packages
import cv2
import sys
import argparse
import difflib
from shutil import copyfile
import os
import numpy as np

# Import the HVF_Object class
from hvf_extraction_script.hvf_data.hvf_object import Hvf_Object

# Import logger class to handle any messages:
from hvf_extraction_script.utilities.logger import Logger

# Import general file functions:
from hvf_extraction_script.utilities.file_utils import File_Utils

# Import tester class:
from hvf_extraction_script.hvf_manager.hvf_test import Hvf_Test

# Default directory for unit tests:
default_unit_test_dir = "default"


# Construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-i", "--image", required=False, help="path to input HVF image file to test")
ap.add_argument("-d", "--dicom", required=False, help="path to input DICOM file to test")
ap.add_argument("-t", "--test", nargs=2, required=False)
ap.add_argument("-a", "--add_test_case", nargs=4, required=False, help="adds input hvf image to test cases")
args = vars(ap.parse_args())


# Set up the logger module:
# debug_level = Logger.DEBUG_FLAG_INFO;
debug_level = Logger.DEBUG_FLAG_WARNING
# debug_level = Logger.DEBUG_FLAG_DEBUG;
msg_logger = Logger.get_logger().set_logger_level(debug_level)


###############################################################################
# SINGLE IMAGE TESTING ########################################################
###############################################################################

# If we are passed in an image, read it and show results
if args["image"]:

    hvf_image = File_Utils.read_image_from_file(args["image"])
    Hvf_Test.test_single_image(hvf_image)


###############################################################################
# DICOM FILE TESTING ##########################################################
###############################################################################
if args["dicom"]:

    hvf_dicom = File_Utils.read_dicom_from_file(args["dicom"])
    hvf_obj = Hvf_Object.get_hvf_object_from_dicom(hvf_dicom)
    print(hvf_obj.get_pretty_string())


###############################################################################
# ADD NEW UNIT TESTS ##########################################################
###############################################################################


# If given a new file, add to the unit test to the specified collection. This
# will use the current version of Hvf_Object to generate the expected result
elif args["add_test_case"]:

    if not (len(args["add_test_case"]) == 4):
        Logger.get_logger().log_msg(
            Logger.DEBUG_FLAG_ERROR,
            "Incorrect number of arguments, needs 4 (test_name, test_type, ref_data, test_data)",
        )
    else:

        test_name = args["add_test_case"][0]
        test_type = args["add_test_case"][1]
        ref_data_path = args["add_test_case"][2]
        test_data_path = args["add_test_case"][3]

        Hvf_Test.add_unit_test(test_name, test_type, ref_data_path, test_data_path)


###############################################################################
# BULK UNIT TESTING ###########################################################
###############################################################################

# If flag, then do unit tests:
elif args["test"]:

    # Assume argument is the testing directory. Make sure its in format of directory
    if not (len(args["test"]) == 2):
        Logger.get_logger().log_msg(
            Logger.DEBUG_FLAG_ERROR, "Incorrect number of arguments, needs 2 (test_name, test_type)"
        )
    else:

        dir = args["test"][0]
        test_type = args["test"][1]

        Hvf_Test.test_unit_tests(dir, test_type)
