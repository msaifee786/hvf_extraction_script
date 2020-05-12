###############################################################################
# hvf_export.py
#
# Description:
#	Code for exporting HVF objects to CSV/other excel-compatible format
#	See code for ordering/column info
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

# General purpose file functions:
from hvf_extraction_script.utilities.file_utils import File_Utils
from hvf_extraction_script.utilities.regex_utils import Regex_Utils

# Import logger class to handle any messages:
from hvf_extraction_script.utilities.logger import Logger;

# Import the HVF_Object class
from hvf_extraction_script.hvf_data.hvf_object import Hvf_Object;
from hvf_extraction_script.hvf_data.hvf_plot_array import Hvf_Plot_Array;
from hvf_extraction_script.hvf_data.hvf_value import Hvf_Value;
from hvf_extraction_script.hvf_data.hvf_perc_icon import Hvf_Perc_Icon;

# Include editing modules:
from hvf_extraction_script.hvf_manager.hvf_editor import Hvf_Editor;



class Hvf_Export:

	###############################################################################
	# VARIABLE/CONSTANT DECLARATIONS: #############################################
	###############################################################################
	CELL_DELIMITER = "\t";

	###############################################################################
	# HELPER FUNCTIONS ############################################################
	###############################################################################

	###############################################################################
	# For converting plots into strings
	def convert_plot_to_delimited_string(plot_obj, laterality, delimiter):


		# Total deviation Percentile array:
		plot_array = plot_obj.get_plot_array();

		# Transpose if left:
		#if (laterality == "Left"):
		#	plot_array = Hvf_Editor.transpose_array(plot_array);

		plot_array_string = Hvf_Plot_Array.get_array_string(plot_array, plot_obj.get_icon_type(), delimiter);
		plot_array_string = plot_array_string.replace("\n\n", delimiter);

		# Lastly, we know that there's usually a trailing newline in the plot
		# array string, which will become a delimiter character. Remove it.
		plot_array_string = plot_array_string.rstrip(delimiter);

		# TODO: Remove spaces (values put spaces to print pretty, so need to remove)

		return plot_array_string;


	###############################################################################
	# For converting hvf objects to delimited strings
	# Always constructs string the same way:
	# 1. Metadata (per order in argument list of keys)
	# 2. Raw value plot
	# 3. Total deviation value plot
	# 4. Total deviation percentile plot
	# 5. Pattern deviation value plot
	# 6. Pattern deviation percentile plot

	def convert_hvf_obj_to_delimited_string(hvf_obj, metadata_key_list, delimiter):

		# Declare our data list to store the info
		data_list = [];

		plot_size = 100;

		# First, grab the metadata fields
		for i in range(len(metadata_key_list)):

			# Append the field to the list
			data_list.append(hvf_obj.metadata.get(metadata_key_list[i]));


		# Next, grab the plots:
		# (Transpose as necessary)
		laterality = hvf_obj.metadata.get(Hvf_Object.KEYLABEL_LATERALITY);


		# Raw plot:
		raw_vals = Hvf_Export.convert_plot_to_delimited_string(hvf_obj.raw_value_array, laterality, delimiter);

		# Total deviation value array:
		tdv_vals = Hvf_Export.convert_plot_to_delimited_string(hvf_obj.abs_dev_value_array, laterality, delimiter);

		# Total deviation Percentile array:
		tdp_vals = Hvf_Export.convert_plot_to_delimited_string(hvf_obj.abs_dev_percentile_array, laterality, delimiter);

		# Need to handle pattern plots separately, because it is possible they are not
		# generated

		pdv_vals = "";
		pdp_vals = "";


		if (hvf_obj.pat_dev_value_array.is_pattern_not_generated()):
			# Not generated, just fill with blanks:
			pdv_vals = delimiter.join([""] * plot_size);
			pdp_vals = delimiter.join([""] * plot_size)

		else:
			# Pattern is generated, so can convert to string as usual
			pdv_vals = Hvf_Export.convert_plot_to_delimited_string(hvf_obj.pat_dev_value_array, laterality, delimiter);
			pdp_vals = Hvf_Export.convert_plot_to_delimited_string(hvf_obj.pat_dev_percentile_array, laterality, delimiter);

		# Add our plot strings (remember, order matters here - correlate with headers above)
		data_list.append(raw_vals);
		data_list.append(tdv_vals);
		data_list.append(tdp_vals);
		data_list.append(pdv_vals);
		data_list.append(pdp_vals);

		# Lastly, generate our return line by interlacing it with delimiter:
		return_line = delimiter.join(data_list);

		return return_line;




	###############################################################################
	# BULK HVF OBJECT EXPORTING ###################################################
	###############################################################################

	###############################################################################
	# Given a dict of file_name->hvf objects, creates a delimited string containing
	# all the data (for export to a spreadsheet file). Delimiter specified in the
	# class code.

	def export_hvf_list_to_spreadsheet(dict_of_hvf):

		# First, generate headers. Major categories of data:
		# 1. Filename source
		# 2. Metadata
		# 3. Raw plot
		# 4. Absolute plots
		# 5. Pattern plots
		# Use keylabel list from Hvf_Object to maintain order/completeness
		metadata_header_list = Hvf_Object.METADATA_KEY_LIST.copy();

		# HEADERS FOR PLOTS. Easiest way is to hard code it. Not very elegant, though.

		plot_size = 100
		raw_val_list = [None] * plot_size
		tdv_list = [None] * plot_size
		tdp_list = [None] * plot_size
		pdv_list = [None] * plot_size
		pdp_list = [None] * plot_size

		for i in range(0, plot_size):
			raw_val_list[i] = "raw" + str(i);
			tdv_list[i] = "tdv" + str(i);
			tdp_list[i] = "tdp" + str(i);
			pdv_list[i] = "pdv" + str(i);
			pdp_list[i] = "pdp" + str(i);

		# Construct our header list
		headers_list = ['file_name'] + metadata_header_list + raw_val_list + tdv_list + tdp_list + pdv_list + pdp_list

		# And construct our return array:
		string_list = [];
		string_list.append(Hvf_Export.CELL_DELIMITER.join(headers_list))

		# Now, iterate for each HVF object and pull the data:
		for file_name in dict_of_hvf:

			# Grab hvf_obj:
			hvf_obj = dict_of_hvf[file_name];

			Logger.get_logger().log_msg(Logger.DEBUG_FLAG_SYSTEM, "Converting File {}".format(file_name));

			# Convert to string:
			hvf_obj_line = file_name + Hvf_Export.CELL_DELIMITER + Hvf_Export.convert_hvf_obj_to_delimited_string(hvf_obj, metadata_header_list, Hvf_Export.CELL_DELIMITER);

			#hvf_obj_line = Regex_Utils.clean_nonascii(hvf_obj_line)

			# And add line to the running list:
			string_list.append(hvf_obj_line);



		# Finally, return joined string:
		return "\n".join(string_list);


	###############################################################################
	# SPREADSHEET IMPORTING TO HVF OBJECT DICTIONARY ##############################
	###############################################################################

	############################################################################
	# Given a data string, slurp in file into a list of rows (which are dicts
	# themselves)
	def slurp_string_to_dict_list(data_string):

		return_list = [];

		string_list = data_string.strip("\n").split("\n")

		header_list = string_list.pop(0).split(Hvf_Export.CELL_DELIMITER);

		for line in string_list:

			line_data = line.split(Hvf_Export.CELL_DELIMITER);

			line_dict = dict(zip(header_list, line_data))

			return_list.append(line_dict)

		return return_list;


	###############################################################################
	# Given a line, generate the HVF object from the data

	def get_hvf_object_from_line(line):

		line, raw_plot = Hvf_Export.get_hvf_plot_from_line(line, Hvf_Plot_Array.PLOT_RAW, Hvf_Plot_Array.PLOT_VALUE)
		line, tdv_plot = Hvf_Export.get_hvf_plot_from_line(line, Hvf_Plot_Array.PLOT_TOTAL_DEV, Hvf_Plot_Array.PLOT_VALUE)
		line, tdp_plot = Hvf_Export.get_hvf_plot_from_line(line, Hvf_Plot_Array.PLOT_TOTAL_DEV, Hvf_Plot_Array.PLOT_PERC)
		line, pdv_plot = Hvf_Export.get_hvf_plot_from_line(line, Hvf_Plot_Array.PLOT_PATTERN_DEV, Hvf_Plot_Array.PLOT_VALUE)
		line, pdp_plot = Hvf_Export.get_hvf_plot_from_line(line, Hvf_Plot_Array.PLOT_PATTERN_DEV, Hvf_Plot_Array.PLOT_PERC)

		# Clean up metadata:
		for key in line.keys():
			line[key] = line.get(key).replace('\"', "").strip()

		hvf_obj = Hvf_Object(line, raw_plot, tdv_plot, pdv_plot, tdp_plot, pdp_plot, None);

		return hvf_obj;


	def get_hvf_plot_from_line(line, plot_type, icon_type):

		plot_name = ""
		plot_values_array = 0;


		if (plot_type == Hvf_Plot_Array.PLOT_RAW):
			plot_name = "raw";
			plot_array = np.zeros((10, 10), dtype=Hvf_Value);

		if (plot_type == Hvf_Plot_Array.PLOT_TOTAL_DEV):
			if (icon_type == Hvf_Plot_Array.PLOT_VALUE):
				plot_name = "tdv";
				plot_array = np.zeros((10, 10), dtype=Hvf_Value);

			if (icon_type == Hvf_Plot_Array.PLOT_PERC):
				plot_name = "tdp";
				plot_array = np.zeros((10, 10), dtype=Hvf_Perc_Icon);

		if (plot_type == Hvf_Plot_Array.PLOT_PATTERN_DEV):
			if (icon_type == Hvf_Plot_Array.PLOT_VALUE):
				plot_name = "pdv";
				plot_array = np.zeros((10, 10), dtype=Hvf_Value);

			if (icon_type == Hvf_Plot_Array.PLOT_PERC):
				plot_name = "pdp"
				plot_array = np.zeros((10, 10), dtype=Hvf_Perc_Icon);


		is_blank = True;
		for i in range(0, 100):
			header_name = plot_name + str(i);

			data_point = line.pop(header_name).replace(" ", "");

			if (data_point == ""):
				# Empty strings cause issues - replace with space
				data_point = " ";
			else:
				is_blank = False;

			if (icon_type == Hvf_Plot_Array.PLOT_VALUE):
				cell_object = Hvf_Value.get_value_from_display_string(data_point)

			if (icon_type == Hvf_Plot_Array.PLOT_PERC):
				cell_object = Hvf_Perc_Icon.get_perc_icon_from_char(data_point);

			x = int(i % 10);
			y = int(i/10);

			plot_array[x, y] = cell_object;

		if (is_blank and plot_type == Hvf_Plot_Array.PLOT_PATTERN_DEV):
			plot_array = Hvf_Plot_Array.NO_PATTERN_DETECT;

		plot_array_obj = Hvf_Plot_Array(plot_type, icon_type, plot_array, None);

		return line, plot_array_obj;

	###############################################################################
	# Given a dict of file_name->hvf objects, creates a delimited string containing
	# all the data (for export to a spreadsheet file). Delimiter specified in the
	# class code.

	# Given an exported spreadsheet (delimited string), creates a dict of
	# file_name->hvf objects. Inverse function of export.

	def import_hvf_list_from_spreadsheet(delimited_string):

		return_dict = {};

		# We will assume the spreadsheet is of correct format - no error checking
		# This means: columns are of correct names (corresponding to metadata, etc)

		# We assume first line is column header, followed by lines of data
		# First, slurp in entire string into a list of dictionaries to we can
		# process each one by one

		list_of_lines = Hvf_Export.slurp_string_to_dict_list(delimited_string)

		# Now, process each one by one:

		for line in list_of_lines:

			file_name = line.pop('file_name');
			Logger.get_logger().log_msg(Logger.DEBUG_FLAG_SYSTEM, "Reading data for {}".format(file_name));


			hvf_obj = Hvf_Export.get_hvf_object_from_line(line);

			return_dict[file_name] = hvf_obj;

		return return_dict;
