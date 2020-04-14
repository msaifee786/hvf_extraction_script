###############################################################################
# hvf_test.py
#
# Description:
#	Functions for testing the HVF_Object class. There are 3 different things
#	this class does:
#
#		test_single_image:
#		- Demos result from a specific HVF file
#
#		test_unit_tests
#		- Runs unit tests (all of them that are in the folder "hvf_test_cases".
#
#		add_unit_test
#		- Adds a specific HVF image file to unit test cases. The expected result
#		  is generated from the current version of the hvf_object, so this
#		  should only be used when the current version is functional/working.
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

# Import logger class to handle any messages:
from hvf_extraction_script.utilities.logger import Logger;

# General purpose file functions:
from hvf_extraction_script.utilities.file_utils import File_Utils

# Import the HVF_Object class and helper classes
from hvf_extraction_script.hvf_data.hvf_object import Hvf_Object;
from hvf_extraction_script.hvf_data.hvf_perc_icon import Hvf_Perc_Icon;
from hvf_extraction_script.hvf_data.hvf_value import Hvf_Value;
from hvf_extraction_script.hvf_data.hvf_plot_array import Hvf_Plot_Array

# Import metric calculators:
from hvf_extraction_script.hvf_manager.hvf_metric_calculator import Hvf_Metric_Calculator;



class Hvf_Test:

	# Unit test folders/names for images and serialization texts:
	UNIT_TEST_MASTER_PATH = "hvf_test_cases/";

	UNIT_TEST_IMAGE_DIR = "image_plots/";
	UNIT_TEST_SERIALIZATION_DIR = "serialized_plots/";


	###############################################################################
	# HELPER FUNCTIONS  ###########################################################
	###############################################################################

	# Helper for constructing image dir and serialization dir (for test cases)
	@staticmethod
	def construct_image_dir(sub_dir):

		return Hvf_Test.UNIT_TEST_MASTER_PATH + sub_dir + Hvf_Test.UNIT_TEST_IMAGE_DIR;

	@staticmethod
	def construct_serialization_dir(sub_dir):

		return Hvf_Test.UNIT_TEST_MASTER_PATH + sub_dir + Hvf_Test.UNIT_TEST_SERIALIZATION_DIR;

	@staticmethod
	def construct_master_test_dir(sub_dir):

		return Hvf_Test.UNIT_TEST_MASTER_PATH + sub_dir;


	# Helper function for comparing two plots - expected plot and actual plot
	# Assumes 10x10 structure
	@staticmethod
	def compare_plots(expected, actual):

		# Keep count of how many mismatches there are
		fail_count = 0

		# Keep running string of display string
		fail_string_list = [];

		# Assume they are of the same size 10x10 - if not, this will fail
		for c in range(10):
			for r in range(10):

				val = np.asscalar(actual.get_plot_array()[c, r]);
				exp_val = np.asscalar(expected.get_plot_array()[c, r]);
				# Check for equality:
				if not(val.is_equal(exp_val)):

					# Failed - increase count, add to string
					fail_count = fail_count+1;

					exp_val_str = "";
					val_str = "";

					string = "--> Element (" + str(c) + ", " + str(r) + ") - expected " + exp_val.get_display_string() + ", actual " + val.get_display_string();
					fail_string_list.append(string);

		# Return the results
		return fail_count, fail_string_list;

	# Helper function for counting non-empty elements within a plots
	# For use in error rate analysis
	@staticmethod
	def count_val_nonempty_elements(plot):

		# If no plot, just count this as 1 element
		if (plot.is_pattern_not_generated()):
			return 1;

		# Keep count of how many nonempty elements there are
		element_count = 0

		# Assume they are of the same size 10x10 - if not, this will fail
		for c in range(10):
			for r in range(10):

				if not (np.asscalar(plot.get_plot_array()[c, r]).get_value() == Hvf_Value.VALUE_NO_VALUE):
					element_count = element_count+1

		# Return the results
		return element_count;

	@staticmethod
	def count_perc_nonempty_elements(plot):

		# If no plot, just count this as 1 element
		if (plot.is_pattern_not_generated()):
			return 1;

		# Keep count of how many nonempty elements there are
		element_count = 0

		# Assume they are of the same size 10x10 - if not, this will fail
		for c in range(10):
			for r in range(10):

				if not (np.asscalar(plot.get_plot_array()[c, r]).get_enum() == Hvf_Perc_Icon.PERC_NO_VALUE):
					element_count = element_count+1

		# Return the results
		return element_count;

	###############################################################################
	# SINGLE IMAGE TESTING ########################################################
	###############################################################################
	@staticmethod
	def test_single_image(hvf_image):
		# Load image

		# Set up the logger module:
		debug_level = Logger.DEBUG_FLAG_SYSTEM;
		#debug_level = Logger.DEBUG_FLAG_DEBUG;
		msg_logger = Logger.get_logger().set_logger_level(debug_level);

		# Instantiate hvf object:
		Logger.get_logger().log_time("Single HVF image extraction time", Logger.TIME_START)
		hvf_obj = Hvf_Object.get_hvf_object_from_image(hvf_image);

		debug_level = Logger.DEBUG_FLAG_TIME;
		msg_logger = Logger.get_logger().set_logger_level(debug_level);

		Logger.get_logger().log_time("Single HVF image extraction time", Logger.TIME_END)

		# Print the display strings:
		print(hvf_obj.get_pretty_string());

		# Get a serialization string of object:
		serialization = hvf_obj.serialize_to_json();

		# Print serialization:
		print(serialization);


		# Test to make sure serialization works:
		hvf_obj2 = Hvf_Object.get_hvf_object_from_text(serialization);

		serialization2 = hvf_obj2.serialize_to_json();


		if (serialization == serialization2):
			Logger.get_logger().log_msg(Logger.DEBUG_FLAG_SYSTEM, "Passed serialization/deserialization consistency");

			# Check to see if we can release saved images without error:
			hvf_obj.release_saved_image();
			hvf_obj2.release_saved_image();
			Logger.get_logger().log_msg(Logger.DEBUG_FLAG_SYSTEM, "Passed releasing saved images");
		else:
			Logger.get_logger().log_msg(Logger.DEBUG_FLAG_SYSTEM, "FAILED serialization/deserialization consistency ==============");

			print(serialization);
			Logger.get_logger().log_msg(Logger.DEBUG_FLAG_SYSTEM, "=====");
			print(serialization2);

			# Check to see if we can release saved images without error:
			hvf_obj.release_saved_image();
			hvf_obj2.release_saved_image();

			#for line in difflib.unified_diff(serialization, serialization2, lineterm=''):
			#	print(line);


		# Test HVF Metric calculator:
		Logger.get_logger().log_msg(Logger.DEBUG_FLAG_SYSTEM, "Global CIGTS TDP Score: " + str(Hvf_Metric_Calculator.get_global_cigts_tdp_score(hvf_obj)));

		if hvf_obj.pat_dev_percentile_array.is_pattern_not_generated():
			pdp_cigts =  "Cannot calculate as pattern not generated"
		else:
			pdp_cigts =  str(Hvf_Metric_Calculator.get_global_cigts_pdp_score(hvf_obj))
		Logger.get_logger().log_msg(Logger.DEBUG_FLAG_SYSTEM, "Global CIGTS PDP Score: " + pdp_cigts);

		# Need to have wait for window instantiation IF the code generates frames - it does
		# when debugging. Comment for now
		#cv2.waitKey(0);
		cv2.destroyAllWindows();

		return "";

	###############################################################################
	# BULK UNIT TESTING ###########################################################
	###############################################################################


	# Do unit tests of a specific directory
	@staticmethod
	def test_unit_tests(sub_dir):

		# Set up the logger module:
		debug_level = Logger.DEBUG_FLAG_SYSTEM;
		msg_logger = Logger.get_logger().set_logger_level(debug_level);

		# TODO: Error check to make sure that sub_dir exists
		master_test_path = Hvf_Test.construct_master_test_dir(sub_dir);

		if not os.path.isdir(master_test_path):
			# This path does not exist!
			Logger.get_logger().log_msg(Logger.DEBUG_FLAG_ERROR, "Unit test directory \'" + sub_dir + "\' does not exist");
			return "";


		test_image_path = Hvf_Test.construct_image_dir(sub_dir);
		serialization_path = Hvf_Test.construct_serialization_dir(sub_dir);


		# Declare variable to keep track of times, errors, etc
		# Will be a list of raw data --> we will calculate metrics at the end
		testing_data_list = [];


		# For each image in the test folder:
		for hvf_image_name in os.listdir(test_image_path):

			# Skip hidden files:
			if hvf_image_name.startswith('.'):
				continue;

			# Then, find corresponding serialization text file
			filename_root, ext = os.path.splitext(hvf_image_name);

			Logger.get_logger().log_msg(debug_level, "================================================================================");
			Logger.get_logger().log_msg(debug_level, "Starting test: " + filename_root);

			# Declare our testing_data dictionary to keep track of data:
			# Vals = count of total values
			# Errors: count of errors
			# Metadata errors are stored as list of tuples (expected, actual)
			testing_data_dict = {
				"time" : 0,
				"metadata_vals" : 0,
				"metadata_errors" : [],
				"value_plot_vals" : 0,
				"value_plot_errors" : 0,
				"perc_plot_vals" : 0,
				"perc_plot_errors" : 0

			};


			# Load image, convert to an hvf_obj
			hvf_image = File_Utils.read_image_from_file(test_image_path + hvf_image_name)


			Logger.get_logger().log_time( "Test " + filename_root, Logger.TIME_START);
			hvf_obj = Hvf_Object.get_hvf_object_from_image(hvf_image);
			time_elapsed = Logger.get_logger().log_time( "Test " + filename_root, Logger.TIME_END);


			testing_data_dict["time"] = time_elapsed;

			serialization_file_name = serialization_path + filename_root + ".txt";
			serialization = File_Utils.read_text_from_file(serialization_file_name);

			# Check for equality
			serialized_obj = hvf_obj.serialize_to_json();

			# Print if passed or not; if not, print the diff
			if (hvf_obj.equals(Hvf_Object.get_hvf_object_from_text(serialization))):
				Logger.get_logger().log_msg(debug_level, "Test " + filename_root + ": PASSED");

				# Need to count number of vals in metadata, value and perc plots
				testing_data_dict["metadata_vals"] = len(hvf_obj.metadata);
				testing_data_dict["value_plot_vals"] = Hvf_Test.count_val_nonempty_elements(hvf_obj.abs_dev_value_array) + Hvf_Test.count_val_nonempty_elements(hvf_obj.pat_dev_value_array);
				testing_data_dict["perc_plot_vals"] = Hvf_Test.count_perc_nonempty_elements(hvf_obj.abs_dev_percentile_array) + Hvf_Test.count_perc_nonempty_elements(hvf_obj.pat_dev_percentile_array);

			else:
				Logger.get_logger().log_msg(debug_level, "Test " + filename_root + ": FAILED ==============================")

				# Compare each field between the object and the expected result, so we can
				# comparison data:
				test_hvf_obj = Hvf_Object.get_hvf_object_from_text(serialization);

				# Compare metadata:
				metadata = hvf_obj.metadata;
				test_metadata = test_hvf_obj.metadata;

				# Iterate through the keys, if mismatch then print and flip the flag; otherwise
				# if we iterate through all and no mismatch, declare full match
				metadata_fail_cnt = 0;
				metadata_fail_str_list = [];

				full_match = True
				for key in test_metadata:

					# Count as we go:
					testing_data_dict["metadata_vals"] = testing_data_dict["metadata_vals"]+1;

					exp_val = test_metadata[key];
					val = metadata.get(key, "<No value>");

					if not(exp_val == val):
						metadata_fail_cnt = metadata_fail_cnt + 1;
						fail_str = "Key: " + str(key) + " - expected: " + str(exp_val) + ", actual: " + str(val);
						metadata_fail_str_list.append(fail_str)

						metadata_error = (exp_val, val);
						testing_data_dict["metadata_errors"].append(metadata_error);

				# Print the results:
				if (metadata_fail_cnt == 0):
					Logger.get_logger().log_msg(debug_level, "- Metadata: FULL MATCH");

				else:
					Logger.get_logger().log_msg(debug_level, "- Metadata MISMATCH COUNT: " + str(metadata_fail_cnt));

					for i in range(len(metadata_fail_str_list)):
						Logger.get_logger().log_msg(debug_level, "--> " + metadata_fail_str_list[i]);


				# Compare raw value plots:
				actual = hvf_obj.raw_value_array;
				expected = test_hvf_obj.raw_value_array

				fail_count, fail_string_list = Hvf_Test.compare_plots(expected, actual);

				total_val_count = Hvf_Test.count_val_nonempty_elements(hvf_obj.raw_value_array);


				testing_data_dict["value_plot_vals"] = testing_data_dict["value_plot_vals"]+total_val_count;
				testing_data_dict["value_plot_errors"] = testing_data_dict["value_plot_errors"]+fail_count;

				# Print the results:
				if (fail_count == 0):
					Logger.get_logger().log_msg(debug_level, "- Raw Value Plot: FULL MATCH");
				else:
					Logger.get_logger().log_msg(debug_level, "- Raw Value Plot MISMATCH COUNT: " + str(fail_count));
					for i in range(len(fail_string_list)):
						Logger.get_logger().log_msg(debug_level,fail_string_list[i]);

				# Next compare value and perc plots:

				# Absolute val:
				actual = hvf_obj.abs_dev_value_array;
				expected = test_hvf_obj.abs_dev_value_array

				fail_count, fail_string_list = Hvf_Test.compare_plots(expected, actual);

				total_val_count = Hvf_Test.count_val_nonempty_elements(hvf_obj.abs_dev_value_array);


				testing_data_dict["value_plot_vals"] = testing_data_dict["value_plot_vals"]+total_val_count;
				testing_data_dict["value_plot_errors"] = testing_data_dict["value_plot_errors"]+fail_count;

				# Print the results:
				if (fail_count == 0):
					Logger.get_logger().log_msg(debug_level, "- Total Deviation Value Plot: FULL MATCH");
				else:
					Logger.get_logger().log_msg(debug_level, "- Total Deviation Value Plot MISMATCH COUNT: " + str(fail_count));
					for i in range(len(fail_string_list)):
						Logger.get_logger().log_msg(debug_level,fail_string_list[i]);

				# Pattern val:
				actual = hvf_obj.pat_dev_value_array;
				expected = test_hvf_obj.pat_dev_value_array

				# Need to check if pattern plot has been generated, or if fields are too depressed
				if (type(actual.plot_array) == type(expected.plot_array)):

					if (actual.is_pattern_not_generated()):

						# They are both in agreement, no pattern detected

						fail_count = 0;
						fail_string_list = [];
						total_val_count = 1;

					else:

						# Both are arrays, and we can compare as usual
						fail_count, fail_string_list = Hvf_Test.compare_plots(expected, actual);
						total_val_count = Hvf_Test.count_val_nonempty_elements(actual);


				else:
					# The two types are in disagreement
					if (actual.is_pattern_not_generated()):

						# They are in disagreement -- actual is no pattern detect, but we expected an array

						fail_string_list.append("Extracted NO PATTERN, but expected a pattern percentile array");
						total_val_count = Hvf_Test.count_val_nonempty_elements(expected);
						fail_count = total_val_count;


					else:

						# They are in disagreement -- actual is an array, but we didn't expect one
						fail_string_list.append("Extracted a pattern percentile array, but expected NO PATTERN");
						total_val_count = Hvf_Test.count_val_nonempty_elements(actual);
						fail_count = total_val_count;

				testing_data_dict["value_plot_vals"] = testing_data_dict["value_plot_vals"]+total_val_count;
				testing_data_dict["value_plot_errors"] = testing_data_dict["value_plot_errors"]+fail_count;

				# Print the results:
				if (fail_count == 0):
					Logger.get_logger().log_msg(debug_level, "- Pattern Deviation Value Plot: FULL MATCH");

				else:
					Logger.get_logger().log_msg(debug_level, "- Pattern Deviation Value Plot MISMATCH COUNT: " + str(fail_count));
					for i in range(len(fail_string_list)):
						Logger.get_logger().log_msg(debug_level,fail_string_list[i]);

				# Absolute perc:
				actual = hvf_obj.abs_dev_percentile_array;
				expected = test_hvf_obj.abs_dev_percentile_array

				fail_count, fail_string_list = Hvf_Test.compare_plots(expected, actual);

				total_val_count = Hvf_Test.count_perc_nonempty_elements(hvf_obj.abs_dev_percentile_array);

				testing_data_dict["perc_plot_vals"] = testing_data_dict["perc_plot_vals"]+total_val_count;
				testing_data_dict["perc_plot_errors"] = testing_data_dict["perc_plot_errors"]+fail_count;


				# Print the results:
				if (fail_count == 0):
					Logger.get_logger().log_msg(debug_level, "- Total Deviation Percentile Plot: FULL MATCH");
				else:
					Logger.get_logger().log_msg(debug_level, "- Total Deviation Percentile Plot MISMATCH COUNT: " + str(fail_count));
					for i in range(len(fail_string_list)):
						Logger.get_logger().log_msg(debug_level,fail_string_list[i]);


				# Pattern perc:
				actual = hvf_obj.pat_dev_percentile_array;
				expected = test_hvf_obj.pat_dev_percentile_array


				# Need to check if pattern plot has been generated, or if fields are too depressed


				if (type(actual.plot_array) == type(expected.plot_array)):

					if ((type(actual.plot_array) == str) and (str(actual.plot_array) == Hvf_Object.NO_PATTERN_DETECT)):

						# They are both in agreement, no pattern detected

						fail_count = 0;
						fail_string_list = [];
						total_val_count = 1;

					else:

						# Both are arrays, and we can compare as usual
						fail_count, fail_string_list = Hvf_Test.compare_plots(expected, actual);
						total_val_count = Hvf_Test.count_perc_nonempty_elements(actual);


				else:
					# The two types are in disagreement

					if ((type(actual.plot_array) == str) and (str(actual.plot_array) == Hvf_Object.NO_PATTERN_DETECT)):

						# They are in disagreement -- actual is no pattern detect, but we expected an array

						fail_string_list.append("Extracted NO PATTERN, but expected a pattern percentile array");
						total_val_count = Hvf_Test.count_perc_nonempty_elements(expected);
						fail_count = total_val_count;


					else:

						# They are in disagreement -- actual is an array, but we didn't expect one
						fail_string_list.append("Extracted a pattern percentile array, but expected NO PATTERN");
						total_val_count = Hvf_Test.count_perc_nonempty_elements(actual);
						fail_count = total_val_count;


				testing_data_dict["perc_plot_vals"] = testing_data_dict["perc_plot_vals"]+total_val_count;
				testing_data_dict["perc_plot_errors"] = testing_data_dict["perc_plot_errors"]+fail_count;


				# Print the results:
				if (fail_count == 0):
					Logger.get_logger().log_msg(debug_level, "- Pattern Deviation Percentile Plot: FULL MATCH");
				else:
					Logger.get_logger().log_msg(debug_level, "- Pattern Deviation Percentile Plot MISMATCH COUNT: " + str(fail_count));
					for i in range(len(fail_string_list)):
						Logger.get_logger().log_msg(debug_level,fail_string_list[i]);


				Logger.get_logger().log_msg(debug_level, "END Test " + filename_root + " FAILURE REPORT =====================")

			testing_data_list.append(testing_data_dict);

		# Now, process our data:

		# Things to evaluate/list:
		# - Total number of tests
		# - Average time to extract data
		# - Number/percentage of metadata errors
		# - Number/percentage of value plot errors
		# - Number/percentage of percentile plot errors

		Logger.get_logger().log_msg(debug_level, "================================================================================");
		Logger.get_logger().log_msg(debug_level, "UNIT TEST AGGREGATE METRICS:")

		num_tests = len(testing_data_list);

		Logger.get_logger().log_msg(debug_level, "Total number of tests: " + str(num_tests))

		list_of_times = list(map(lambda x: x["time"], testing_data_list));
		average_time = round(sum(list_of_times)/len(list_of_times))

		Logger.get_logger().log_msg(debug_level, "Average extraction time per report: " + str(average_time) + "ms")

		Logger.get_logger().log_msg(debug_level, "")

		metadata_total = sum(list(map(lambda x: x["metadata_vals"], testing_data_list)));
		metadata_errors = sum(list(map(lambda x: len(x["metadata_errors"]), testing_data_list)));
		metadata_error_percentage = round(metadata_errors/metadata_total, 3)

		Logger.get_logger().log_msg(debug_level, "Total number of metadata fields: " + str(metadata_total))
		Logger.get_logger().log_msg(debug_level, "Total number of metadata field errors: " + str(metadata_errors))
		Logger.get_logger().log_msg(debug_level, "Metadata field error rate: " + str(metadata_error_percentage))

		Logger.get_logger().log_msg(debug_level, "")

		value_total = sum(list(map(lambda x: x["value_plot_vals"], testing_data_list)));
		value_errors = sum(list(map(lambda x: x["value_plot_errors"], testing_data_list)));
		value_error_percentage = round(value_errors/value_total, 3)

		Logger.get_logger().log_msg(debug_level, "Total number of value data points: " + str(value_total))
		Logger.get_logger().log_msg(debug_level, "Total number of value data point errors: " + str(value_errors))
		Logger.get_logger().log_msg(debug_level, "Value data point error rate: " + str(value_error_percentage))

		Logger.get_logger().log_msg(debug_level, "")

		perc_total = sum(list(map(lambda x: x["perc_plot_vals"], testing_data_list)));
		perc_errors = sum(list(map(lambda x: x["perc_plot_errors"], testing_data_list)));
		perc_error_percentage = round(perc_errors/perc_total, 3)

		Logger.get_logger().log_msg(debug_level, "Total number of percentile data points: " + str(perc_total))
		Logger.get_logger().log_msg(debug_level, "Total number of percentile data point errors: " + str(perc_errors))
		Logger.get_logger().log_msg(debug_level, "Percentile data point error rate: " + str(perc_error_percentage))


		return "";

	###############################################################################
	# ADD NEW UNIT TESTS ##########################################################
	###############################################################################

	# If given a new file, add this to the unit test. This will use the current version to
	# generate the expected result
	@staticmethod
	def add_unit_test(src_path, test_path):
		# Load image
		#src_path = args["add_test_case"];
		hvf_image = File_Utils.read_image_from_file(src_path)

		# Get hvf object and serialized it
		hvf_obj = Hvf_Object.get_hvf_object_from_image(hvf_image);
		serialization = hvf_obj.serialize_to_json();

		# Add the test cases to the test folders:

		# First, check if we have this master directory or not
		master_test_path = Hvf_Test.construct_master_test_dir(test_path);

		# Construct the target path for the test folders:
		test_image_path = Hvf_Test.construct_image_dir(test_path);
		serialization_path = Hvf_Test.construct_serialization_dir(test_path)

		# If they don't exist yet, create them
		if not os.path.isdir(master_test_path):
			Logger.get_logger().log_msg(Logger.DEBUG_FLAG_SYSTEM, "Making new unit test directory: " + test_path);

			os.mkdir(master_test_path);
			os.mkdir(test_image_path);
			os.mkdir(serialization_path);

		# First, get file name
		path, filename = os.path.split(src_path)
		filename_root, ext = os.path.splitext(filename);

		# Save HVF image:
		copyfile(src_path, test_image_path+filename)

		# Save HVF serialization:
		File_Utils.write_string_to_file(serialization, serialization_path+filename_root+".txt")

		Logger.get_logger().log_msg(Logger.DEBUG_FLAG_SYSTEM, "Added unit test case: " + filename);

		return "";
