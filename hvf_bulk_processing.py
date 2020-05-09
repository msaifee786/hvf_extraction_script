###############################################################################
# hvf_bulk_processing.py
#
# Description:
#	Given a directory of HVF files, outputs them in a CSV file format. See
#	code for ordering/column info
#
#	Usage:
#		python hvf_bulk_processing -i <directory_of_images>
#			Outputs a spreadsheet TSV file "output_spreadsheet.tsv" from images
#
#		python hvf_bulk_processing -t <directory_of_text_files>
#			Outputs a spreadsheet TSV file "output_spreadsheet.tsv" from JSON
#			text files
#
#		python hvf_bulk_processing -s <directory_of_images>
#			Outputs a directory of JSON text files into directory
#			"serialized_hvf"; makes directory if does not exist
#
#		python hvf_bulk_processing -f <path_to_tsv_file>
#			Outputs a directory of JSON text files into directory
#			"serialized_hvf"; makes directory if does not exist
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
#import dlib

# Import the HVF_Object class
from hvf_extraction_script.hvf_data.hvf_object import Hvf_Object;

# Import logger class to handle any messages:
from hvf_extraction_script.utilities.logger import Logger;

# Import file utilities
from hvf_extraction_script.utilities.file_utils import File_Utils;

# Import tester class:
from hvf_extraction_script.hvf_manager.hvf_export import Hvf_Export;

# Construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-i", "--image_directory", required=False,
	help="path to directory of images to convert to spreadsheet")
ap.add_argument("-t", "--text_directory", required=False,
	help="path to directory of text files to convert to spreadsheet")
ap.add_argument("-s", "--save_images", required=False,
	help="path to directory of image files to read and save as text documents")
ap.add_argument("-f", "--import_file", required=False,
	help="path to TSV file to import and save as text documents")
args = vars(ap.parse_args())


###############################################################################
# HELPER METHODS ##############################################################
###############################################################################

###############################################################################
# From a directory of images, returns a dictionary of HVF objects:

def get_dict_of_hvf_objs_from_imgs(directory):

	# Read in images from directory:
	list_of_image_file_extensions = [".bmp", ".jpg", ".jpeg", ".png"];
	list_of_img_paths = File_Utils.get_files_within_dir(directory, list_of_image_file_extensions);

	dict_of_hvf_objs = {};

	for hvf_img_path in list_of_img_paths:

		path, filename = os.path.split(hvf_img_path)
		Logger.get_logger().log_msg(Logger.DEBUG_FLAG_SYSTEM, "Reading HVF image " + filename);
		hvf_img = File_Utils.read_image_from_file(hvf_img_path);

		hvf_obj = Hvf_Object.get_hvf_object_from_image(hvf_img);
		hvf_obj.release_saved_image();
		dict_of_hvf_objs[filename] = hvf_obj;

	return dict_of_hvf_objs;

###############################################################################
# From a directory of text files, returns a dictionary of HVF objects:

def get_dict_of_hvf_objs_from_text(directory):

	# Read in text files from directory:
	list_of_file_extensions = [".txt"];
	list_of_txt_paths = File_Utils.get_files_within_dir(directory, list_of_file_extensions);

	dict_of_hvf_objs = {};

	for hvf_txt_path in list_of_txt_paths:

		path, filename = os.path.split(hvf_txt_path)
		Logger.get_logger().log_msg(Logger.DEBUG_FLAG_SYSTEM, "Reading HVF text file " + filename);

		hvf_txt = File_Utils.read_text_from_file(hvf_txt_path);

		hvf_obj = Hvf_Object.get_hvf_object_from_text(hvf_txt);

		dict_of_hvf_objs[filename] = hvf_obj

	return dict_of_hvf_objs;



###############################################################################
# BULK UNIT TESTING ###########################################################
###############################################################################

Logger.set_logger_level(Logger.DEBUG_FLAG_SYSTEM);

# If flag, then do unit tests:
if (args["image_directory"]):

	# Grab the argument directory for readability
	directory = args["image_directory"];

	dict_of_hvf_objs = get_dict_of_hvf_objs_from_imgs(directory);

	return_string = Hvf_Export.export_hvf_list_to_spreadsheet(dict_of_hvf_objs)

	File_Utils.write_string_to_file(return_string, "output_spreadsheet.tsv")

elif (args["text_directory"]):

	# Grab the argument directory for readability
	directory = args["text_directory"];

	Logger.get_logger().log_msg(Logger.DEBUG_FLAG_SYSTEM, "========== START READING ALL TEXT FILES ==========");
	dict_of_hvf_objs = get_dict_of_hvf_objs_from_text(directory);

	Logger.get_logger().log_msg(Logger.DEBUG_FLAG_SYSTEM, "========== FINISHED READING ALL TEXT FILES ==========");

	Logger.get_logger().log_msg(Logger.DEBUG_FLAG_SYSTEM, "========== START EXPORT ==========");

	return_string = Hvf_Export.export_hvf_list_to_spreadsheet(dict_of_hvf_objs)

	Logger.get_logger().log_msg(Logger.DEBUG_FLAG_SYSTEM, "========== WRITING EXPORT SPREADSHEET ==========");

	File_Utils.write_string_to_file(return_string, "output_spreadsheet.tsv")

elif (args["save_images"]):

	directory = args["save_images"];

	save_dir = "serialized_hvfs"

	if not os.path.isdir(save_dir):
		Logger.get_logger().log_msg(Logger.DEBUG_FLAG_SYSTEM, "Making new save directory: " + save_dir);

		os.mkdir(save_dir);

	list_of_image_file_extensions = [".bmp", ".jpg", ".jpeg", ".png"];
	list_of_img_paths = File_Utils.get_files_within_dir(directory, list_of_image_file_extensions);

	for hvf_img_path in list_of_img_paths:

		path, filename = os.path.split(hvf_img_path)
		Logger.get_logger().log_msg(Logger.DEBUG_FLAG_SYSTEM, "Reading HVF image " + filename);
		hvf_img = File_Utils.read_image_from_file(hvf_img_path);


		try:
			hvf_obj = Hvf_Object.get_hvf_object_from_image(hvf_img);

			file_path = os.path.join(save_dir, str(filename)+".txt");

			Logger.get_logger().log_msg(Logger.DEBUG_FLAG_SYSTEM, "Writing text serialization file " + filename);
			File_Utils.write_string_to_file(hvf_obj.serialize_to_json(), file_path)

		except:
			Logger.get_logger().log_msg(Logger.DEBUG_FLAG_SYSTEM, "============= FAILURE on serializing " + filename);

elif (args["import_file"]):

	path_to_tsv_file = args["import_file"];

	save_dir = "serialized_hvfs"

	if not os.path.isdir(save_dir):
		Logger.get_logger().log_msg(Logger.DEBUG_FLAG_SYSTEM, "Making new save directory: " + save_dir);

		os.mkdir(save_dir);

	tsv_file_string = File_Utils.read_text_from_file(path_to_tsv_file);


	dict_of_hvf_objs = Hvf_Export.import_hvf_list_from_spreadsheet(tsv_file_string);

	for filename in dict_of_hvf_objs.keys():
		hvf_obj = dict_of_hvf_objs.get(filename)

		try:
			file_path = os.path.join(save_dir, str(filename));

			Logger.get_logger().log_msg(Logger.DEBUG_FLAG_SYSTEM, "Writing text serialization file " + filename);
			File_Utils.write_string_to_file(hvf_obj.serialize_to_json(), file_path)

		except:
			Logger.get_logger().log_msg(Logger.DEBUG_FLAG_SYSTEM, "============= FAILURE on serializing " + filename);

else:
	Logger.get_logger().log_msg(Logger.DEBUG_FLAG_ERROR, "No input directory given");
