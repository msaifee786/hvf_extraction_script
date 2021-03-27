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
from datetime import datetime

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

	# Unit test folders/names:
	UNIT_TEST_MASTER_PATH = "hvf_test_cases";


	UNIT_TEST_IMAGE_VS_SERIALIZATION = "image_vs_serialization";
	UNIT_TEST_IMAGE_VS_DICOM = "image_vs_dicom";
	UNIT_TEST_SERIALIZATION_VS_DICOM = "serialization_vs_dicom";
	UNIT_TEST_SERIALIZATION_VS_SERIALIZATION = "serialization_vs_serialization";

	UNIT_TEST_REFERENCE_DIR = "reference_data"
	UNIT_TEST_TEST_DIR = "test_data"


	UNIT_TEST_IMAGE_DIR = "image_plots";
	UNIT_TEST_SERIALIZATION_DIR = "serialized_plots";


	###############################################################################
	# FILE MANAGEMENT HELPER FUNCTIONS  ###########################################
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

	###############################################################################
	# TESTING HELPER FUNCTIONS  ###################################################
	###############################################################################

	# Helper function for comparing two plots - expected plot and actual plot
	# Assumes 10x10 structure
	@staticmethod
	def compare_plots(test_name, expected, actual):
		# Keep running string of display string
		fail_string_list = [];

		# Keep list of all failures
		fail_list = []

		# Assume they are of the same size 10x10 - if not, this will fail
		for c in range(10):
			for r in range(10):

				val = actual.get_plot_array()[c, r];
				exp_val = expected.get_plot_array()[c, r];
				# Check for equality:
				if not(val.is_equal(exp_val)):

					exp_val_str = exp_val.get_display_string();
					val_str = val.get_display_string();

					fail_dict = {
						"test_name" : test_name,
						"location" : "{}, {}".format(c,r),
						"expected" : exp_val.get_display_string(),
						"actual" : val.get_display_string()

					}
					fail_list.append(fail_dict)

					string = "--> Element (" + str(c) + ", " + str(r) + ") - expected " + exp_val.get_display_string() + ", actual " + val.get_display_string();
					fail_string_list.append(string);

		# Return the results
		return fail_list, fail_string_list;

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

				if not (plot.get_plot_array()[c, r].get_value() == Hvf_Value.VALUE_NO_VALUE):
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

				if not (plot.get_plot_array()[c, r].get_enum() == Hvf_Perc_Icon.PERC_NO_VALUE):
					element_count = element_count+1

		# Return the results
		return element_count;

	@staticmethod
	def compare_metadata_dicts(test_name, test_metadata, ref_metadata):

		num_metadata_fields = 0;
		metadata_errors = []
		metadata_fail_str_list = [];

		key_to_func_dict = {
			Hvf_Object.KEYLABEL_NAME: Hvf_Test.compare_names,
			Hvf_Object.KEYLABEL_DOB: Hvf_Test.compare_dates,
			Hvf_Object.KEYLABEL_ID: Hvf_Test.compare_ids,
			Hvf_Object.KEYLABEL_TEST_DATE: Hvf_Test.compare_dates,
			Hvf_Object.KEYLABEL_LATERALITY: Hvf_Test.compare_laterality,
			Hvf_Object.KEYLABEL_FOVEA: Hvf_Test.compare_fovea,
			Hvf_Object.KEYLABEL_FIXATION_LOSS: Hvf_Test.compare_fl,
			Hvf_Object.KEYLABEL_FALSE_POS: Hvf_Test.compare_fp_fn,
			Hvf_Object.KEYLABEL_FALSE_NEG: Hvf_Test.compare_fp_fn,
			Hvf_Object.KEYLABEL_TEST_DURATION: Hvf_Test.compare_test_duration,
			Hvf_Object.KEYLABEL_FIELD_SIZE: Hvf_Test.compare_field_size,
			Hvf_Object.KEYLABEL_STRATEGY: Hvf_Test.compare_strategy,
			Hvf_Object.KEYLABEL_PUPIL_DIAMETER: Hvf_Test.compare_pupil_diameter,
			Hvf_Object.KEYLABEL_RX: Hvf_Test.compare_rx,
			Hvf_Object.KEYLABEL_MD: Hvf_Test.compare_md_psd,
			Hvf_Object.KEYLABEL_PSD: Hvf_Test.compare_md_psd,
			Hvf_Object.KEYLABEL_VFI: Hvf_Test.compare_vfi
		}

		for key in key_to_func_dict.keys():
			comparison_func = key_to_func_dict.get(key);

			num_metadata_fields = num_metadata_fields+1;
			ref_data = ref_metadata.get(key, "<No Value>")
			test_data = test_metadata.get(key, "<No Value>")
			if not (comparison_func(ref_data, test_data)):
				metadata_fail_str_list.append("Key: {} - expected: {}, actual: {}".format(str(key), str(ref_data), str(test_data)))
				fail_dict = {
					"test_name" : test_name,
					"field_name" : key,
					"expected" : ref_data,
					"actual" : test_data

				}
				metadata_errors.append(fail_dict);

		return_dict = {
			"num_metadata_fields": num_metadata_fields,
			"metadata_errors": metadata_errors,
			"fail_string_list": metadata_fail_str_list

		};

		return return_dict;


	def compare_names(ref_data, test_data):

		ref_name = ref_data.lower().replace(", ", ",")
		ref_name = ref_name.replace(",", " ")

		test_name = test_data.lower().replace(", ", ",")
		test_name = test_name.replace(",", " ")

		bool = ref_name == test_name;

		return bool;

	def compare_dates(ref_data, test_data):

		ref_date = Hvf_Test.get_datetime_obj(ref_data);
		test_date = Hvf_Test.get_datetime_obj(test_data);

		return ref_date == test_date;

	def compare_ids(ref_data, test_data):
		ref_data = str(ref_data);

		while (len(ref_data) < 8):
			ref_data = "0" + ref_data;

		test_data = str(test_data);

		while (len(test_data) < 8):
			test_data = "0" + test_data;

		return ref_data == test_data;

	def compare_laterality(ref_data, test_data):
		bool = ref_data.lower() == test_data.lower();

		return bool;

	def compare_fovea(ref_data, test_data):
		return ref_data == test_data;

	def compare_fl(ref_data, test_data):
		try:
			ref_data = ref_data.replace("x", "")
			test_data = test_data.replace("x", "")

		except:
			ref_data = ref_data
			test_data = test_data
		bool = (ref_data == test_data)
		return ref_data == test_data;

	def compare_fp_fn(ref_data, test_data):
		ref_data = ref_data.replace("%", "")
		ref_data = ref_data.replace("x", "")
		ref_data = ref_data.replace("X", "")
		test_data = test_data.replace("%", "")
		test_data = test_data.replace("x", "")
		test_data = test_data.replace("X", "")
		return ref_data == test_data;

	def compare_test_duration(ref_data, test_data):

		try:
			ref_data_list = ref_data.split(":")
			test_data_list = test_data.split(":")

			bool = (int(ref_data_list[0]) == int(test_data_list[0])) and (int(ref_data_list[1]) == int(test_data_list[1]))

		except:
			bool = (ref_data == test_data);

		return bool;

	def compare_field_size(ref_data, test_data):
		return ref_data == test_data;

	def compare_strategy(ref_data, test_data):
		bool = ref_data.lower().replace("-", " ") == test_data.lower().replace("-", " ");

		return bool;

	def compare_pupil_diameter(ref_data, test_data):
		try:
			ref_data = float(ref_data)
			test_data = float(test_data)

		except:
			ref_data = ref_data
			test_data = test_data

		bool = (ref_data == test_data);
		return bool;

	def compare_rx(ref_data, test_data):


		try:
			ref_rx = Hvf_Test.get_rx_array(ref_data);
			test_rx = Hvf_Test.get_rx_array(test_data);

			bool = (ref_rx[0] == test_rx[0]) and (ref_rx[1] == test_rx[1]) and (ref_rx[2] == test_rx[2]);

		except:
			bool = ref_data == test_data;


		return bool

	def compare_md_psd(ref_data, test_data):
		try:
			bool = (float(ref_data) == float(test_data))
		except:
			bool = (ref_data == test_data)
		return bool;

	def compare_vfi(ref_data, test_data):
		ref_data = ref_data.replace("%", "")
		test_data = test_data.replace("%", "")
		return ref_data == test_data;

	def get_datetime_obj(date_string):

		# Date options:
		# MM-DD-YYYY
		# MM/DD/YYYY
		# MM/DD/YY
		# Mon DD, YYYY
		# YYYY-MM-DD

		date_parse_string_list = [
			"%m-%d-%Y",
			"%-m-%-d-%Y",
			"%d-%b-%y",
			"%m/%d/%Y",
			"%m/%d/%y",
			"%-m/%-d/%Y",
			"%b %d, %Y",
			"%Y-%m-%d"
		]

		for parse_string in date_parse_string_list:
			try:
				datetime_obj = datetime.strptime(date_string, parse_string);

				# If only 2 digit year, it will extrapolate to 20xx, which is likely
				# not what we want. If year is in future, correct to 1900s.
				if (datetime.today() <= datetime_obj):
					datetime_obj = datetime_obj.replace(year=datetime_obj.year - 100)

				return datetime_obj;
			except:
				continue;

		return date_string;

	def get_rx_array(rx_data):

		rx_data = rx_data.lower().replace(" ", "");

		sphere_array = rx_data.split("ds");

		sphere = float(sphere_array[0]);

		try:

			cyl_array = sphere_array[1].split("dc");

			cyl = float(cyl_array[0]);

			axis_array = cyl_array[1].split("x");

			axis = int(axis_array[1]);

		except:
			cyl = "";
			axis = "";

		return (sphere, cyl, axis);


	def test_hvf_obj(test_name, reference_hvf_obj, test_hvf_obj, time_elapsed):

		testing_msgs = [];
		testing_msgs.append("================================================================================");
		testing_msgs.append("Starting test: " + test_name)
		if (time_elapsed > 0):
			testing_msgs.append("Time for extraction: {} ms".format(str(time_elapsed)));

		# Declare our testing_data dictionary to keep track of data:
		# Vals = count of total values
		# Errors: count of errors
		# Metadata errors are stored as list of tuples (expected, actual)
		testing_data_dict = {
			"time" : 0,
			"metadata_vals" : 0,
			"metadata_errors" : [],
			"value_plot_vals" : 0,
			"value_plot_errors" : [],
			"perc_plot_vals" : 0,
			"perc_plot_errors" : []

		};


		# Print if passed or not; if not, print the diff
		if (reference_hvf_obj.equals(test_hvf_obj)):
			testing_msgs.append("Test " + test_name + ": PASSED");

			# Need to count number of vals in metadata, value and perc plots
			testing_data_dict["metadata_vals"] = len(reference_hvf_obj.metadata);
			testing_data_dict["value_plot_vals"] = Hvf_Test.count_val_nonempty_elements(reference_hvf_obj.abs_dev_value_array) + Hvf_Test.count_val_nonempty_elements(reference_hvf_obj.pat_dev_value_array);
			testing_data_dict["perc_plot_vals"] = Hvf_Test.count_perc_nonempty_elements(reference_hvf_obj.abs_dev_percentile_array) + Hvf_Test.count_perc_nonempty_elements(reference_hvf_obj.pat_dev_percentile_array);

		else:
			testing_msgs.append("Test " + test_name + ": FAILED ==============================");

			# Compare each field between the object and the expected result, so we can
			# comparison data:

			# Compare metadata:
			test_metadata = test_hvf_obj.metadata;
			ref_metadata = reference_hvf_obj.metadata;

			# Iterate through the keys, if mismatch then print and flip the flag; otherwise
			# if we iterate through all and no mismatch, declare full match


			# Check each metadata key individually, because comparisons require
			# some processing

			metadata_error_dict = Hvf_Test.compare_metadata_dicts(test_name, test_metadata, ref_metadata);
			testing_data_dict["metadata_vals"] = metadata_error_dict.get("num_metadata_fields")
			testing_data_dict["metadata_errors"] = metadata_error_dict.get("metadata_errors")
			metadata_fail_cnt = len(metadata_error_dict.get("metadata_errors"));
			metadata_fail_str_list = metadata_error_dict.get("fail_string_list")

			# Print the results:
			if (metadata_fail_cnt == 0):
				testing_msgs.append("- Metadata: FULL MATCH");

			else:
				testing_msgs.append("- Metadata MISMATCH COUNT: " + str(metadata_fail_cnt));

				for i in range(len(metadata_fail_str_list)):
					testing_msgs.append("--> " + metadata_fail_str_list[i]);


			# Compare raw value plots:
			actual = test_hvf_obj.raw_value_array;
			expected = reference_hvf_obj.raw_value_array

			fail_list, fail_string_list = Hvf_Test.compare_plots(test_name, expected, actual);

			total_val_count = Hvf_Test.count_val_nonempty_elements(reference_hvf_obj.raw_value_array);
			raw_val_count = total_val_count; ###

			testing_data_dict["value_plot_vals"] = testing_data_dict["value_plot_vals"]+total_val_count;
			testing_data_dict["value_plot_errors"] = testing_data_dict["value_plot_errors"] + fail_list;

			# Print the results:
			if (len(fail_list) == 0):
				testing_msgs.append("- Raw Value Plot: FULL MATCH");
			else:
				testing_msgs.append("- Raw Value Plot MISMATCH COUNT: " + str(len(fail_list)));
				for i in range(len(fail_string_list)):
					testing_msgs.append(fail_string_list[i]);

			# Next compare value and perc plots:

			# Absolute val:
			actual = test_hvf_obj.abs_dev_value_array;
			expected = reference_hvf_obj.abs_dev_value_array

			fail_list, fail_string_list = Hvf_Test.compare_plots(test_name, expected, actual);

			total_val_count = Hvf_Test.count_val_nonempty_elements(reference_hvf_obj.abs_dev_value_array);
			total_dev_val_count = total_val_count ###

			testing_data_dict["value_plot_vals"] = testing_data_dict["value_plot_vals"]+total_val_count;
			testing_data_dict["value_plot_errors"] = testing_data_dict["value_plot_errors"]+fail_list;

			# Print the results:
			if (len(fail_list) == 0):
				testing_msgs.append("- Total Deviation Value Plot: FULL MATCH");
			else:
				testing_msgs.append("- Total Deviation Value Plot MISMATCH COUNT: " + str(len(fail_list)));
				for i in range(len(fail_string_list)):
					testing_msgs.append(fail_string_list[i]);

			# Pattern val:
			actual = test_hvf_obj.pat_dev_value_array;
			expected = reference_hvf_obj.pat_dev_value_array

			# Need to check if pattern plot has been generated, or if fields are too depressed
			if (type(actual.plot_array) == type(expected.plot_array)):

				if (actual.is_pattern_not_generated()):

					# They are both in agreement, no pattern detected

					fail_list = [];
					fail_string_list = [];
					total_val_count = 1;

				else:

					# Both are arrays, and we can compare as usual
					fail_list, fail_string_list = Hvf_Test.compare_plots(test_name, expected, actual);
					#total_val_count = Hvf_Test.count_val_nonempty_elements(actual);
					total_val_count = Hvf_Test.count_val_nonempty_elements(expected);


			else:
				# The two types are in disagreement
				if (actual.is_pattern_not_generated()):

					# They are in disagreement -- actual is no pattern detect, but we expected an array

					fail_string_list.append("Extracted NO PATTERN, but expected a pattern percentile array");
					total_val_count = Hvf_Test.count_val_nonempty_elements(expected);
					fail_element = {
						"test_name" : test_name,
						"location" : " ",
						"expected" : "Extracted NO PATTERN, but expected a pattern percentile array",
						"actual" : "Extracted NO PATTERN, but expected a pattern percentile array"
					}
					fail_list = [fail_element] * total_val_count

				else:

					# They are in disagreement -- actual is an array, but we didn't expect one
					fail_string_list.append("Extracted a pattern percentile array, but expected NO PATTERN");
					#total_val_count = Hvf_Test.count_val_nonempty_elements(actual);
					total_val_count = Hvf_Test.count_val_nonempty_elements(expected);
					fail_element = {
						"test_name" : test_name,
						"location" : " ",
						"expected" : "Extracted a pattern percentile array, but expected NO PATTERN",
						"actual" : "Extracted a pattern percentile array, but expected NO PATTERN"
					}
					fail_list = [fail_element] * total_val_count

			pat_dev_val_count = total_val_count ###
			testing_data_dict["value_plot_vals"] = testing_data_dict["value_plot_vals"]+total_val_count;
			testing_data_dict["value_plot_errors"] = testing_data_dict["value_plot_errors"]+fail_list;

			# Print the results:
			if (len(fail_list) == 0):
				testing_msgs.append("- Pattern Deviation Value Plot: FULL MATCH");

			else:
				testing_msgs.append("- Pattern Deviation Value Plot MISMATCH COUNT: " + str(len(fail_list)));
				for i in range(len(fail_string_list)):
					testing_msgs.append(fail_string_list[i]);

			# Absolute perc:
			actual = test_hvf_obj.abs_dev_percentile_array;
			expected = reference_hvf_obj.abs_dev_percentile_array

			fail_list, fail_string_list = Hvf_Test.compare_plots(test_name, expected, actual);

			total_val_count = Hvf_Test.count_perc_nonempty_elements(reference_hvf_obj.abs_dev_percentile_array);
			total_dev_perc_count = total_val_count

			testing_data_dict["perc_plot_vals"] = testing_data_dict["perc_plot_vals"]+total_val_count;
			testing_data_dict["perc_plot_errors"] = testing_data_dict["perc_plot_errors"]+fail_list;


			# Print the results:
			if (len(fail_list) == 0):
				testing_msgs.append("- Total Deviation Percentile Plot: FULL MATCH");
			else:
				testing_msgs.append("- Total Deviation Percentile Plot MISMATCH COUNT: " + str(len(fail_list)));
				for i in range(len(fail_string_list)):
					testing_msgs.append(fail_string_list[i]);


			# Pattern perc:
			actual = test_hvf_obj.pat_dev_percentile_array;
			expected = reference_hvf_obj.pat_dev_percentile_array


			# Need to check if pattern plot has been generated, or if fields are too depressed


			if (type(actual.plot_array) == type(expected.plot_array)):

				if ((type(actual.plot_array) == str) and (str(actual.plot_array) == Hvf_Object.NO_PATTERN_DETECT)):

					# They are both in agreement, no pattern detected

					fail_list = [];
					fail_string_list = [];
					total_val_count = 1;

				else:

					# Both are arrays, and we can compare as usual
					fail_list, fail_string_list = Hvf_Test.compare_plots(test_name, expected, actual);
					#total_val_count = Hvf_Test.count_perc_nonempty_elements(actual);
					total_val_count = Hvf_Test.count_perc_nonempty_elements(expected);


			else:
				# The two types are in disagreement

				if ((type(actual.plot_array) == str) and (str(actual.plot_array) == Hvf_Object.NO_PATTERN_DETECT)):

					# They are in disagreement -- actual is no pattern detect, but we expected an array

					fail_string_list.append("Extracted NO PATTERN, but expected a pattern percentile array");
					total_val_count = Hvf_Test.count_perc_nonempty_elements(expected);
					fail_element = {
						"test_name" : test_name,
						"location" : " ",
						"expected" : "Extracted NO PATTERN, but expected a pattern percentile array",
						"actual" : "Extracted NO PATTERN, but expected a pattern percentile array"
					}
					fail_list = [fail_element] * total_val_count


				else:

					# They are in disagreement -- actual is an array, but we didn't expect one
					fail_string_list.append("Extracted a pattern percentile array, but expected NO PATTERN");
					#total_val_count = Hvf_Test.count_perc_nonempty_elements(actual);
					total_val_count = Hvf_Test.count_perc_nonempty_elements(expected);
					fail_element = {
						"test_name" : test_name,
						"location" : " ",
						"expected" : "Extracted a pattern percentile array, but expected NO PATTERN",
						"actual" : "Extracted a pattern percentile array, but expected NO PATTERN"
					}
					fail_list = [fail_element] * total_val_count

			pat_dev_perc_count = total_val_count ###;
			testing_data_dict["perc_plot_vals"] = testing_data_dict["perc_plot_vals"]+total_val_count;
			testing_data_dict["perc_plot_errors"] = testing_data_dict["perc_plot_errors"]+fail_list;


			# Print the results:
			if (len(fail_list) == 0):
				testing_msgs.append("- Pattern Deviation Percentile Plot: FULL MATCH");
			else:
				testing_msgs.append("- Pattern Deviation Percentile Plot MISMATCH COUNT: " + str(len(fail_list)));
				for i in range(len(fail_string_list)):
					testing_msgs.append(fail_string_list[i]);


			testing_msgs.append("END Test " + test_name + " FAILURE REPORT =====================")

			print_array = [test_name, raw_val_count, total_dev_val_count, total_dev_perc_count, pat_dev_val_count, pat_dev_perc_count]

			print("\t".join(list(map(lambda x: str(x), print_array))));

		return testing_data_dict, testing_msgs;



	def print_unit_test_aggregate_metrics(testing_data_list):
		debug_level = Logger.DEBUG_FLAG_SYSTEM;

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

		if (average_time > 0):
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
		value_errors = sum(list(map(lambda x: len(x["value_plot_errors"]), testing_data_list)));
		value_error_percentage = round(value_errors/value_total, 3)

		Logger.get_logger().log_msg(debug_level, "Total number of value data points: " + str(value_total))
		Logger.get_logger().log_msg(debug_level, "Total number of value data point errors: " + str(value_errors))
		Logger.get_logger().log_msg(debug_level, "Value data point error rate: " + str(value_error_percentage))

		Logger.get_logger().log_msg(debug_level, "")

		perc_total = sum(list(map(lambda x: x["perc_plot_vals"], testing_data_list)));
		perc_errors = sum(list(map(lambda x: len(x["perc_plot_errors"]), testing_data_list)));
		perc_error_percentage = round(perc_errors/perc_total, 3)

		Logger.get_logger().log_msg(debug_level, "Total number of percentile data points: " + str(perc_total))
		Logger.get_logger().log_msg(debug_level, "Total number of percentile data point errors: " + str(perc_errors))
		Logger.get_logger().log_msg(debug_level, "Percentile data point error rate: " + str(perc_error_percentage))


		return "";

	###############################################################################
	# SINGLE IMAGE TESTING ########################################################
	###############################################################################
	@staticmethod
	def test_single_image(hvf_image):
		# Load image

		# Set up the logger module:
		debug_level = Logger.DEBUG_FLAG_SYSTEM;
		#debug_level = Logger.DEBUG_FLAG_INFO;
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
	def test_unit_tests(sub_dir, test_type):

		# Set up the logger module:
		debug_level = Logger.DEBUG_FLAG_ERROR;
		msg_logger = Logger.get_logger().set_logger_level(debug_level);

		# Error check to make sure that sub_dir exists
		test_dir_path = os.path.join(Hvf_Test.UNIT_TEST_MASTER_PATH, test_type, sub_dir);
		test_data_path = os.path.join(test_dir_path, Hvf_Test.UNIT_TEST_TEST_DIR)
		reference_data_path = os.path.join(test_dir_path, Hvf_Test.UNIT_TEST_REFERENCE_DIR)

		if (not os.path.isdir(test_dir_path)):
			# This path does not exist!
			Logger.get_logger().log_msg(Logger.DEBUG_FLAG_ERROR, "Unit test directory \'{}\' does not exist".format(test_dir_path));
			return "";

		if (not os.path.isdir(test_data_path)):
			# This path does not exist!
			Logger.get_logger().log_msg(Logger.DEBUG_FLAG_ERROR, "Unit test directory \'{}\' does not exist".format(test_data_path));
			return "";

		if (not os.path.isdir(reference_data_path)):
			# This path does not exist!
			Logger.get_logger().log_msg(Logger.DEBUG_FLAG_ERROR, "Unit test directory \'{}\' does not exist".format(reference_data_path));
			return "";

		Logger.get_logger().log_msg(debug_level, "================================================================================");
		Logger.get_logger().log_msg(debug_level, "Starting HVF Unit Testing");
		Logger.get_logger().log_msg(debug_level, "Test Type: {}".format(test_type));
		Logger.get_logger().log_msg(debug_level, "Unit Test Name: {}".format(sub_dir));

		# Declare variable to keep track of times, errors, etc
		# Will be a list of raw data --> we will calculate metrics at the end
		aggregate_testing_data_dict = {};

		# For each file in the test folder:
		for hvf_file in os.listdir(test_data_path):

			# Skip hidden files:
			if hvf_file.startswith('.'):
				continue;

			# Then, find corresponding reference file
			filename_root, ext = os.path.splitext(hvf_file);

			reference_hvf_obj = None;
			test_hvf_obj = None;

			# How to generate hvf obj from these files depends on what type of test:


			if (test_type == Hvf_Test.UNIT_TEST_IMAGE_VS_SERIALIZATION):
				# Load image, convert to an hvf_obj
				hvf_image_path = os.path.join(test_data_path, hvf_file)
				hvf_image = File_Utils.read_image_from_file(hvf_image_path);

				Logger.get_logger().log_time( "Test " + filename_root, Logger.TIME_START);
				test_hvf_obj = Hvf_Object.get_hvf_object_from_image(hvf_image);
				time_elapsed = Logger.get_logger().log_time( "Test " + filename_root, Logger.TIME_END);

				serialization_path = os.path.join(reference_data_path, filename_root + ".txt");
				serialization = File_Utils.read_text_from_file(serialization_path);
				reference_hvf_obj = Hvf_Object.get_hvf_object_from_text(serialization);


			elif (test_type == Hvf_Test.UNIT_TEST_IMAGE_VS_DICOM):
				# Load image, convert to an hvf_obj
				hvf_image_path = os.path.join(test_data_path, hvf_file)
				hvf_image = File_Utils.read_image_from_file(hvf_image_path);

				Logger.get_logger().log_time( "Test " + filename_root, Logger.TIME_START);
				test_hvf_obj = Hvf_Object.get_hvf_object_from_image(hvf_image);
				time_elapsed = Logger.get_logger().log_time( "Test " + filename_root, Logger.TIME_END);

				dicom_file_path = os.path.join(reference_data_path, filename_root + ".dcm");
				dicom_ds = File_Utils.read_dicom_from_file(dicom_file_path);
				reference_hvf_obj = Hvf_Object.get_hvf_object_from_dicom(dicom_ds);

			elif (test_type == Hvf_Test.UNIT_TEST_SERIALIZATION_VS_DICOM):

				serialization_file_path = os.path.join(test_data_path, hvf_file);
				serialization = File_Utils.read_text_from_file(serialization_file_path);
				test_hvf_obj = Hvf_Object.get_hvf_object_from_text(serialization);

				dicom_file_path = os.path.join(reference_data_path, filename_root + ".dcm");
				dicom_ds = File_Utils.read_dicom_from_file(dicom_file_path);
				reference_hvf_obj = Hvf_Object.get_hvf_object_from_dicom(dicom_ds);

				time_elapsed = 0;


			elif (test_type == Hvf_Test.UNIT_TEST_SERIALIZATION_VS_SERIALIZATION):

				serialization_file_path = os.path.join(test_data_path, hvf_file);
				serialization = File_Utils.read_text_from_file(serialization_file_path);
				test_hvf_obj = Hvf_Object.get_hvf_object_from_text(serialization);

				ref_serialization_path = os.path.join(reference_data_path, filename_root + ".txt");
				ref_serialization = File_Utils.read_text_from_file(ref_serialization_path);
				reference_hvf_obj = Hvf_Object.get_hvf_object_from_text(ref_serialization);

				time_elapsed = 0;


			else:
				Logger.get_logger().log_msg(Logger.DEBUG_FLAG_ERROR, "Unrecognized test type \'{}\'".format(test_type));
				return "";

			testing_data_dict, testing_msgs = Hvf_Test.test_hvf_obj(filename_root, reference_hvf_obj, test_hvf_obj, time_elapsed)
			testing_data_dict["time"] = time_elapsed;

			# Print messages
			#for msg in testing_msgs:
			#	Logger.get_logger().log_msg(debug_level, msg)

			aggregate_testing_data_dict[filename_root] = testing_data_dict;

		Hvf_Test.print_unit_test_aggregate_metrics(aggregate_testing_data_dict.values());

		metadata_error_header_list = ["test_name", "field_name", "expected", "actual"];
		metadata_error_output = "\t".join(metadata_error_header_list) + "\n";
		for test in aggregate_testing_data_dict.keys():
			for error in aggregate_testing_data_dict[test]["metadata_errors"]:
				error_string = "\t".join(error.values()) + "\n";
				metadata_error_output = metadata_error_output + error_string;

		plot_header_list = ["test_name", "location", "expected", "actual"];
		value_plot_error_output = "\t".join(plot_header_list) + "\n";
		for test in aggregate_testing_data_dict.keys():
			for error in aggregate_testing_data_dict[test]["value_plot_errors"]:
				error_string = "\t".join(error.values()) + "\n";
				value_plot_error_output = value_plot_error_output + error_string;

		perc_plot_error_output = "\t".join(plot_header_list) + "\n";
		for test in aggregate_testing_data_dict.keys():
			for error in aggregate_testing_data_dict[test]["perc_plot_errors"]:
				error_string = "\t".join(error.values()) + "\n";
				perc_plot_error_output = perc_plot_error_output + error_string;

		if (True):
			metadata_error_output = metadata_error_output.encode('ascii', 'ignore').decode('unicode_escape')
			File_Utils.write_string_to_file(metadata_error_output, sub_dir + "_metadata_errors.tsv")
			File_Utils.write_string_to_file(value_plot_error_output, sub_dir + "_value_plot_errors.tsv")
			File_Utils.write_string_to_file(perc_plot_error_output, sub_dir + "_perc_plot_errors.tsv")


		return "";

	###############################################################################
	# ADD NEW UNIT TESTS ##########################################################
	###############################################################################

	# If given a new file, add this to the unit test. This will use the current version to
	# generate the expected result
	@staticmethod
	def add_unit_test(test_name, test_type, ref_data_path, test_data_path):

		# Set up the logger module:
		debug_level = Logger.DEBUG_FLAG_ERROR;
		msg_logger = Logger.get_logger().set_logger_level(debug_level);

		# First, check if we have this master directory (and image extraciton test directory) or not
		master_path = Hvf_Test.UNIT_TEST_MASTER_PATH;
		test_type_path = os.path.join(Hvf_Test.UNIT_TEST_MASTER_PATH, test_type);
		test_name_path = os.path.join(Hvf_Test.UNIT_TEST_MASTER_PATH, test_type, test_name);
		test_data_path = os.path.join(test_dir_path, Hvf_Test.UNIT_TEST_TEST_DIR)
		reference_data_path = os.path.join(test_dir_path, Hvf_Test.UNIT_TEST_REFERENCE_DIR)


		# If they don't exist yet, create them
		create_path_if_not_present = master_path
		if not os.path.isdir(create_path_if_not_present):
			Logger.get_logger().log_msg(Logger.DEBUG_FLAG_SYSTEM, "Making new unit test directory: " + create_path_if_not_present);
			os.mkdir(create_path_if_not_present);

		create_path_if_not_present = test_type_path
		if not os.path.isdir(create_path_if_not_present):
			Logger.get_logger().log_msg(Logger.DEBUG_FLAG_SYSTEM, "Making new unit test directory: " + create_path_if_not_present);
			os.mkdir(create_path_if_not_present);

		create_path_if_not_present = test_name_path
		if not os.path.isdir(create_path_if_not_present):
			Logger.get_logger().log_msg(Logger.DEBUG_FLAG_SYSTEM, "Making new unit test directory: " + create_path_if_not_present);
			os.mkdir(create_path_if_not_present);

		create_path_if_not_present = test_data_path
		if not os.path.isdir(create_path_if_not_present):
			Logger.get_logger().log_msg(Logger.DEBUG_FLAG_SYSTEM, "Making new unit test directory: " + create_path_if_not_present);
			os.mkdir(create_path_if_not_present);

		create_path_if_not_present = reference_data_path
		if not os.path.isdir(create_path_if_not_present):
			Logger.get_logger().log_msg(Logger.DEBUG_FLAG_SYSTEM, "Making new unit test directory: " + create_path_if_not_present);
			os.mkdir(create_path_if_not_present);

		# First, get file name
		ref_path, ref_filename = os.path.split(ref_data_path);
		test_path, test_filename = os.path.split(test_data_path);

		# Just make sure that filenames are the same, because when we test them we look for same file name roots
		ref_filename_root, ref_ext = os.path.splitext(ref_filename);
		test_filename_root, test_ext = os.path.splitext(test_filename);

		if not (test_filename_root == ref_filename_root):
			ref_filename = test_filename_root + "." + ref_ext
			Logger.get_logger().log_msg(Logger.DEBUG_FLAG_SYSTEM, "Renaming reference file to {} to match with test file".format(ref_filename));

		# Save the files:
		copyfile(ref_data_path, os.path.join(reference_data_path, ref_filename));
		copyfile(test_data_path, os.path.join(test_data_path, test_filename));

		Logger.get_logger().log_msg(Logger.DEBUG_FLAG_SYSTEM, "Added unit test - TYPE: {}, NAME: {}".format(test_type, test_filename_root));

		return "";
