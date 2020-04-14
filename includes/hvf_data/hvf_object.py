###############################################################################
# hvf_object.py
#
# Description:
#	Class definition for a single HVF object. Given a single HVF printout
#   image object (as a cv2 image ie numpy array), uses opencv image detection
#   and tesseract OCR to read out import data from the printout and stores
#   it in a single hvf object.
#
#   Also supports reading and writing hvf_object to a text string for
#   serialization/deserialization purposes.
#
# Main usage:
#	Call factory methods to instantiate object (don't use initializer). Two
#	main ways to instantiate a new HVF object:
#		- Via HVF printout image - uses openCV image
#		- Via a serialized text string - uses format from this objects serialization
#
#	Major attributes for each object:
#		- Dictionary of metadata (including strategy type, reliability metrics
#		  MD/PSD, etc
#		- Absolute/pattern value deviation plot (as 10x10 arrays)
#		- Absolute/pattern percentile deviation plot (as a 10x10 arrays)
#		--> Percentile plot arrays represent elements using enum values, defined below
#
#	Once an object has be instantiated, can serialize it using method function; this
#	outputs a string that can be saved, and object can be re-instantiated (faster)
#	from this string (see serialization functions)
#
#	Lastly, this object can output display strings for the plots in a human-readable
#	format for convenience
#
#	To Do:
#		- Function to determine laterality by perc/value plots
###############################################################################

# Import necessary packages
import cv2
import sys

# Import some helper packages:
import numpy as np
from functools import reduce

# Import JSON to serialization
import json

# Import regular expression packages
import re
import regex
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from fuzzysearch import find_near_matches

# Import some of our own written modules:

# For error/debug logging:
from includes.utilities.logger import Logger

# General purpose image functions:
from includes.utilities.image_utils import Image_Utils

# Regex utility functions:
from includes.utilities.regex_utils import Regex_Utils

# OCR utility functions:
from includes.utilities.ocr_utils import Ocr_Utils

# For percentile icon detection:
from includes.hvf_data.hvf_perc_icon import Hvf_Perc_Icon

# For number value detection:
from includes.hvf_data.hvf_value import Hvf_Value

# For overall plot detection:
from includes.hvf_data.hvf_plot_array import Hvf_Plot_Array

class Hvf_Object:


	###############################################################################
	# CONSTANTS AND STATIC VARIABLES ##############################################
	###############################################################################

	# Initialization flag
	is_initialized = False;

	###############################################################################
	# Metadata/field labels/enums


	# Array labels:
	KEYLABEL_RAW_VAL_PLOT = 'raw_value_plot';
	KEYLABEL_ABS_VAL_PLOT = 'absolute_value_plot';
	KEYLABEL_PAT_VAL_PLOT = 'pattern_value_plot';
	KEYLABEL_ABS_PERC_PLOT = 'absolute_percentile_plot';
	KEYLABEL_PAT_PERC_PLOT = 'pattern_percentile_plot';


	# Labels:
	KEYLABEL_NAME = 'name';
	KEYLABEL_DOB = 'dob';
	KEYLABEL_TEST_DATE = 'test_date';
	KEYLABEL_LATERALITY = 'laterality';
	KEYLABEL_FOVEA = 'fovea';
	KEYLABEL_FIXATION_LOSS = 'fixation_loss';
	KEYLABEL_FALSE_POS = 'false_pos';
	KEYLABEL_FALSE_NEG = 'false_neg';
	KEYLABEL_TEST_DURATION = 'test_duration'; ###
	KEYLABEL_ID = 'id';
	KEYLABEL_FIELD_SIZE = 'field_size';
	KEYLABEL_STRATEGY = 'strategy';  ###
	KEYLABEL_PUPIL_DIAMETER = 'pupil_diameter';  ###
	KEYLABEL_RX = "rx"; ###
	KEYLABEL_MD = 'md';
	KEYLABEL_PSD = 'psd';
	KEYLABEL_VFI = 'vfi';


	METADATA_KEY_LIST = [
		KEYLABEL_NAME,
		KEYLABEL_DOB,
		KEYLABEL_ID,
		KEYLABEL_TEST_DATE,
		KEYLABEL_LATERALITY,
		KEYLABEL_FOVEA,
		KEYLABEL_FIXATION_LOSS,
		KEYLABEL_FALSE_POS,
		KEYLABEL_FALSE_NEG,
		KEYLABEL_TEST_DURATION,
		KEYLABEL_FIELD_SIZE,
		KEYLABEL_STRATEGY,
		KEYLABEL_PUPIL_DIAMETER,
		KEYLABEL_RX,
		KEYLABEL_MD,
		KEYLABEL_PSD,
		KEYLABEL_VFI
	];

	ABS_PLOT_KEY_LIST = [ KEYLABEL_ABS_VAL_PLOT, KEYLABEL_ABS_PERC_PLOT ];

	PAT_PLOT_KEY_LIST = [ KEYLABEL_PAT_VAL_PLOT, KEYLABEL_PAT_PERC_PLOT ];

	# HVF field size:
	HVF_30_2 = "30-2"
	HVF_24_2 = "24-2"
	HVF_10_2 = "10-2"

	# Laterality
	HVF_OD = "Right"
	HVF_OS = "Left"

	# Strategy
	HVF_FULL_THRESHOLD = "Full Threshold";
	HVF_SITA_STANDARD = "SITA Standard";
	HVF_SITA_FAST = "SITA Fast";

	###############################################################################
	# Value/string to represent no pattern detect
	NO_PATTERN_DETECT = "Pattern Deviation not shown for severely depressed fields";

	###############################################################################
	# Delimiter character - for use in serialization/deserialization
	SERIALIZATION_DELIMITER_CHAR = "|";

	###############################################################################
	# Layout versions:
	HVF_LAYOUT_V1 = "v1";
	HVF_LAYOUT_V2 = "v2";



	###############################################################################
	# CONSTRUCTOR AND FACTORY METHODS #############################################
	###############################################################################

	###############################################################################
	# Initializer method
	# Not to be used publicly - use factory methods instead
	# Takes in pertinent HVF data (metadata, value/perc arrays) and instantiates new HVF
	# object
	def __init__(self, metadata, raw_value_array, abs_dev_val_array, pat_dev_val_array, abs_dev_perc_array, pat_dev_perc_array, image):

		self.metadata = metadata;

		self.raw_value_array = raw_value_array;

		self.abs_dev_value_array = abs_dev_val_array;
		self.pat_dev_value_array = pat_dev_val_array;

		self.abs_dev_percentile_array = abs_dev_perc_array;
		self.pat_dev_percentile_array = pat_dev_perc_array;

		self.image = image;

	###############################################################################
	# Factory method - get new object from HVF image
	# This is the method to call to generate a new HVF object
	# Takes in an OpenCV image object
	@classmethod
	def get_hvf_object_from_image(cls, hvf_image):

		# Initialize any templates/variables if this is first time we are running:
		if (cls.is_initialized is False):
			# Not initialized - initialize now
			cls.initialize_class_vars();


		# First, need to upscale image if its too low resolution (important for older HVF
		# images). Min width is a bit arbitrary but is close to ~300ppi
		width = np.size(hvf_image, 1)
		MIN_HVF_WIDTH = 2500;
		WARNING_HVF_WIDTH = 1000;

		#if (width < WARNING_HVF_WIDTH):
			#Logger.get_logger().log_msg(Logger.DEBUG_FLAG_WARNING, "Resolution low, high risk for detection errors");


		if (width < MIN_HVF_WIDTH):
			scale_factor = MIN_HVF_WIDTH/width;
			hvf_image = cv2.resize(hvf_image, None, fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_CUBIC)

		# preprocess image:
		# Grab grayscale:
		hvf_image_gray = cv2.cvtColor(hvf_image, cv2.COLOR_BGR2GRAY);

		layout_version = Hvf_Object.find_image_layout_version(hvf_image_gray);

		# Get absolute raw value plot:
		raw_value_array = cls.get_abs_raw_val_plot(hvf_image_gray);

		# Get deviation value plots (both absolute and pattern):
		abs_dev_value_array = cls.get_abs_deviation_val_plot(hvf_image_gray);
		pat_dev_value_array = cls.get_pattern_deviation_val_plot(hvf_image_gray);

		# Now, get the deviation percentile plots (both absolute and pattern):
		abs_dev_percentile_array = cls.get_abs_deviation_perc_plot(hvf_image_gray);
		pat_dev_percentile_array = cls.get_pattern_deviation_perc_plot(hvf_image_gray);

		# Get header metadata:
		metadata = cls.get_header_metadata_from_hvf_image(hvf_image_gray, layout_version);

		# Then validate the field size/laterality based on layout of field:
		field_size_laterality_dict = Hvf_Object.get_field_size_laterality_from_plot(abs_dev_value_array);
		metadata.update(field_size_laterality_dict);

		# Then, get the metric metadata (need to know field size):
		metric_metadata = cls.get_metric_metadata_from_hvf_image(hvf_image_gray, layout_version, metadata[Hvf_Object.KEYLABEL_FIELD_SIZE]);
		metadata.update(metric_metadata);

		# Instantiate a new object:
		hvf_obj = Hvf_Object(metadata, raw_value_array, abs_dev_value_array, pat_dev_value_array, abs_dev_percentile_array, pat_dev_percentile_array, hvf_image)

		return hvf_obj;


	###############################################################################
	# Factory method - get new object from text serialization
	# This is the method to call to generate a new object from a 'saved' object
	@classmethod
	def get_hvf_object_from_text(cls, hvf_text):

		# TODO:
		# Perform entire function under a try-catch block -- if any issues, throw
		# a warning log

		# First, convert text (presumed JSON) into python native:
		hvf_dict = json.loads(hvf_text);

		# RAW VALUE PLOT #################################################################

		raw_val_plot_list_by_row = hvf_dict.pop(Hvf_Object.KEYLABEL_RAW_VAL_PLOT);

		# Generate array of plot elements objects:
		raw_val_plot_array = Hvf_Object.get_value_plot_from_row_strings(raw_val_plot_list_by_row);

		# Make a plot wrapper for the array:
		raw_val_plot = Hvf_Plot_Array.get_plot_from_array(Hvf_Plot_Array.PLOT_RAW, Hvf_Plot_Array.PLOT_VALUE, raw_val_plot_array);


		# ABSOLUTE VALUE PLOT ############################################################

		# Get list of strings from JSON:
		abs_val_plot_list_by_row = hvf_dict.pop(Hvf_Object.KEYLABEL_ABS_VAL_PLOT);

		# Generate array of plot elements objects:
		abs_val_plot = Hvf_Object.get_value_plot_from_row_strings(abs_val_plot_list_by_row);

		# Make a plot wrapper for the array:
		total_dev_val_plot = Hvf_Plot_Array.get_plot_from_array(Hvf_Plot_Array.PLOT_TOTAL_DEV, Hvf_Plot_Array.PLOT_VALUE, abs_val_plot);



		# PATTERN VALUE PLOT #############################################################
		# Get list of strings from JSON:
		pat_val_plot_list_by_row = hvf_dict.pop(Hvf_Object.KEYLABEL_PAT_VAL_PLOT);

		# Detect if there is not pattern plot to detect:
		if (pat_val_plot_list_by_row == Hvf_Object.NO_PATTERN_DETECT):
			pat_val_plot = Hvf_Object.NO_PATTERN_DETECT;
		else:

			# If we do indeed have a pattern plot, extract it:
			pat_val_plot = Hvf_Object.get_value_plot_from_row_strings(pat_val_plot_list_by_row);

		# Make a plot wrapper for the array:
		pat_dev_val_plot = Hvf_Plot_Array.get_plot_from_array(Hvf_Plot_Array.PLOT_PATTERN_DEV, Hvf_Plot_Array.PLOT_VALUE, pat_val_plot);




		# ABSOLUTE PERC PLOT #############################################################
		# Get list of strings from JSON:
		abs_perc_plot_list_by_row = hvf_dict.pop(Hvf_Object.KEYLABEL_ABS_PERC_PLOT);

		# Generate array of plot elements objects:
		abs_perc_plot = Hvf_Object.get_perc_plot_from_row_strings(abs_perc_plot_list_by_row);

		# Make a plot wrapper for the array:
		total_dev_perc_plot = Hvf_Plot_Array.get_plot_from_array(Hvf_Plot_Array.PLOT_TOTAL_DEV, Hvf_Plot_Array.PLOT_PERC, abs_perc_plot);



		# PATTERN PERC PLOT ##############################################################
		# Get list of strings from JSON:
		pat_perc_plot_list_by_row = hvf_dict.pop(Hvf_Object.KEYLABEL_PAT_PERC_PLOT);

		# Detect if there is not pattern plot to detect:
		if (pat_perc_plot_list_by_row == Hvf_Object.NO_PATTERN_DETECT):
			pat_perc_plot = Hvf_Object.NO_PATTERN_DETECT;
		else:

			# If we do indeed have a pattern plot, extract it:
			pat_perc_plot = Hvf_Object.get_perc_plot_from_row_strings(pat_perc_plot_list_by_row);

		pat_dev_perc_plot = Hvf_Plot_Array.get_plot_from_array(Hvf_Plot_Array.PLOT_PATTERN_DEV, Hvf_Plot_Array.PLOT_PERC, pat_perc_plot);



		# Remaining items in dictionary assumed to metadata

		# Instantiate a new object:
		hvf_obj = Hvf_Object(hvf_dict, raw_val_plot, total_dev_val_plot, pat_dev_val_plot, total_dev_perc_plot, pat_dev_perc_plot, None)

		return hvf_obj;


	###############################################################################
	# Variable Initialization method - does some preprocessing for variables for
	# ease of calculation
	@classmethod
	def initialize_class_vars(cls):

		Hvf_Plot_Array.initialize_class_vars();
		Hvf_Perc_Icon.initialize_class_vars();
		Hvf_Value.initialize_class_vars();

		# Lastly, flip the flag to indicate initialization has been done
		cls.is_initialized = True;

		return None;



	###############################################################################
	# OBJECT METHODS ##############################################################
	###############################################################################

	###############################################################################
	# Releases saved images (to help save memory)
	def release_saved_image(self):

		self.image = None;

		self.raw_value_array.release_saved_image();

		self.abs_dev_value_array.release_saved_image();
		self.pat_dev_value_array.release_saved_image();

		self.abs_dev_percentile_array.release_saved_image();
		self.pat_dev_percentile_array.release_saved_image();

		return;



	###############################################################################
	# Serializes hvf object - outputs a string to be saved to a file (ie serialization)
	# Allow HVF processing to be saved for quick reading
	# Delimit everything by same character
	def serialize_to_json(self):

		# We essentially create a large dictionary of all the pertinent info, then
		# convert to JSON
		# For ease/reliability of behavior, we convert the arrays to strings and
		# store in the dictionary

		# Make a copy of the dict because we'll be adding new items:
		serialize_dict = self.metadata.copy();

		# Add the abs and pattern value deviation plots:
		# We make an list of strings corresponding to the plot row (ease of readability)

		# Store the row string lists in the serialization dict:
		serialize_dict[Hvf_Object.KEYLABEL_RAW_VAL_PLOT] = self.raw_value_array.get_display_string_list(Hvf_Object.SERIALIZATION_DELIMITER_CHAR);
		serialize_dict[Hvf_Object.KEYLABEL_ABS_VAL_PLOT] = self.abs_dev_value_array.get_display_string_list(Hvf_Object.SERIALIZATION_DELIMITER_CHAR);
		serialize_dict[Hvf_Object.KEYLABEL_PAT_VAL_PLOT] = self.pat_dev_value_array.get_display_string_list(Hvf_Object.SERIALIZATION_DELIMITER_CHAR);
		serialize_dict[Hvf_Object.KEYLABEL_ABS_PERC_PLOT] = self.abs_dev_percentile_array.get_display_string_list(Hvf_Object.SERIALIZATION_DELIMITER_CHAR);
		serialize_dict[Hvf_Object.KEYLABEL_PAT_PERC_PLOT] = self.pat_dev_percentile_array.get_display_string_list(Hvf_Object.SERIALIZATION_DELIMITER_CHAR);

		# Lastly, we convert to JSON string and return that

		return json.dumps(serialize_dict, indent=4);

	###############################################################################
	# Outputs the raw value plot
	def get_display_raw_val_plot_string(self):
		title = "Raw Value Plot: \n";
		return title + self.raw_value_array.get_display_string(" ");

	###############################################################################
	# Outputs the absolute deviation percentile plot
	def get_display_abs_val_plot_string(self):
		title = "Absolute Deviation Value Plot: \n";
		return title + self.abs_dev_value_array.get_display_string(" ");

	###############################################################################
	# Outputs the pattern deviation percentile plot
	def get_display_pat_val_plot_string(self):
		title = "Pattern Deviation Value Plot: ";
		content_string = self.pat_dev_value_array.get_display_string(" ");

		if (content_string.count('\n') > 0):
			title = title + "\n";

		return title + content_string;

	###############################################################################
	# Outputs the absolute deviation percentile plot
	def get_display_abs_perc_plot_string(self):
		title = "Absolute Deviation Percentile Plot: \n";
		return title + self.abs_dev_percentile_array.get_display_string("   ");

	###############################################################################
	# Outputs the pattern deviation percentile plot
	def get_display_pat_perc_plot_string(self):
		title = "Pattern Deviation Percentile Plot: ";
		content_string = self.pat_dev_percentile_array.get_display_string("   ");

		if (content_string.count('\n') > 0):
			title = title + "\n";

		return title + content_string;

	###############################################################################
	# Outputs the entire object's data as a typeset pretty sring
	def get_pretty_string(self):
		ret_string = "";

		# Generate metadata string:
		for key in Hvf_Object.METADATA_KEY_LIST:
			metadata_string = key + ": " + self.metadata.get(key) + "\n";

			ret_string = ret_string + metadata_string;

		ret_string = ret_string + "\n";

		# Then the plot strings:
		ret_string = ret_string + "\n" + self.get_display_raw_val_plot_string();
		ret_string = ret_string + "\n" + self.get_display_abs_val_plot_string();
		ret_string = ret_string + "\n" + self.get_display_pat_val_plot_string();
		ret_string = ret_string + "\n" + self.get_display_abs_perc_plot_string();
		ret_string = ret_string + "\n" + self.get_display_pat_perc_plot_string();

		return ret_string;

	###############################################################################
	# Returns boolean of equality between object and argument
	def equals(self, arg_obj):

		for key in Hvf_Object.METADATA_KEY_LIST:
			if not (self.metadata.get(key) == arg_obj.metadata.get(key)):
				return False;

		if not (self.raw_value_array.get_display_string_list(Hvf_Object.SERIALIZATION_DELIMITER_CHAR) == arg_obj.raw_value_array.get_display_string_list(Hvf_Object.SERIALIZATION_DELIMITER_CHAR)):
			 return False;

		if not (self.abs_dev_value_array.get_display_string_list(Hvf_Object.SERIALIZATION_DELIMITER_CHAR) == arg_obj.abs_dev_value_array.get_display_string_list(Hvf_Object.SERIALIZATION_DELIMITER_CHAR)):
			return False;

		if not (self.pat_dev_value_array.get_display_string_list(Hvf_Object.SERIALIZATION_DELIMITER_CHAR) == arg_obj.pat_dev_value_array.get_display_string_list(Hvf_Object.SERIALIZATION_DELIMITER_CHAR)):
			return False;

		if not (self.abs_dev_percentile_array.get_display_string_list(Hvf_Object.SERIALIZATION_DELIMITER_CHAR) == arg_obj.abs_dev_percentile_array.get_display_string_list(Hvf_Object.SERIALIZATION_DELIMITER_CHAR)):
			return False;

		if not (self.pat_dev_percentile_array.get_display_string_list(Hvf_Object.SERIALIZATION_DELIMITER_CHAR) == arg_obj.pat_dev_percentile_array.get_display_string_list(Hvf_Object.SERIALIZATION_DELIMITER_CHAR)):
			return False;

		return True;


	###############################################################################
	# Given a full image, determines what type of layout it is (v1 vs v2).
	# Implementation: simply looks for "Date of Birth" in top right header -> if
	# found, then v2, otherwise v1
	# Searching done by regex and fuzzy matching
	# Likely will need to be improved in future
	@staticmethod
	def find_image_layout_version(hvf_image):

		return_version = Hvf_Object.HVF_LAYOUT_V1;

		# Recall arguments: (image, y_ratio, y_size, x_ratio, x_size)
		header_slice = Image_Utils.slice_image(hvf_image, 0, 0.15, 0, 0.31)
		header_text = Ocr_Utils.perform_ocr(header_slice);

		partial_fuzz_score = fuzz.partial_ratio("Date of Birth", header_text);

		if (partial_fuzz_score > 50):
			return_version = Hvf_Object.HVF_LAYOUT_V2;

		return return_version;

	###############################################################################
	# DESERIALIZATION HELPER METHODS ##############################################
	###############################################################################

	###############################################################################
	# Given a value plot by rows, returns the constructed value plot:
	@staticmethod
	def get_value_plot_from_row_strings(value_plot_by_row):

		ret_plot = np.zeros((10, 10, 1), dtype=Hvf_Value);

		for ii in range(0, len(value_plot_by_row)):
			row_string = value_plot_by_row[ii];

			row = row_string.split(Hvf_Object.SERIALIZATION_DELIMITER_CHAR);

			for jj in range(0, len(row)):
				num = row[jj];

				# For readability, there is white space in the number string - strip them
				num = num.replace(" ","");

				ret_plot[jj, ii] = Hvf_Value.get_value_from_display_string(num);

		return ret_plot


	###############################################################################
	# Given a perc plot by rows, returns the constructed perc plot:
	@staticmethod
	def get_perc_plot_from_row_strings(perc_plot_by_row):

		# Absolute percentile plot:
		ret_plot = np.zeros((10, 10, 1), dtype=Hvf_Perc_Icon);

		for ii in range(0, len(perc_plot_by_row)):
			row_string = perc_plot_by_row[ii];

			row = row_string.split(Hvf_Object.SERIALIZATION_DELIMITER_CHAR);

			for jj in range(0, len(row)):
				ret_plot[jj, ii] = Hvf_Perc_Icon.get_perc_icon_from_char(row[jj]);

		return ret_plot




	###############################################################################
	# METADATA EXTRACTION METHODS #################################################
	###############################################################################

	###############################################################################
	# Reads header metadata from HVF image:
	@staticmethod
	def get_header_metadata_from_hvf_image(hvf_image_gray, layout_version):

		#hvf_image_gray = Image_Utils.preprocess_image(hvf_image_gray);

		# First, convert grayscale -> black and white, to optimize text detection
		hvf_image_gray = cv2.bitwise_not(cv2.adaptiveThreshold(hvf_image_gray,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY_INV,11,5));

		# We get the metadata by:
		# 1. Slicing image (as finely as possible, to optimize OCR)
		# 2. Applying OCR to get text
		# 3. Concatenating all the OCR texts
		# 4. Using regex to extract the data

		# Do this for header (for most metadata) and bottom right (for MD/PSD)
		# Declare our full metadata text, to regex later:
		metadata_text = "";

		# For top header:
		# We slice in quarters then OCR each separately
		# This is for efficiency, because we can eliminate which quarters we don't need to
		# process based on what metadata we want

		# Header 1 slice:
		# Height: 0.0 -> 0.25
		# Width: 0.0 -> 0.31
		# Contains: Name, ID, HVF size, reliability data, fovea, etc

		# Recall arguments: (image, y_ratio, y_size, x_ratio, x_size)
		header_slice_image1 = Image_Utils.slice_image(hvf_image_gray, 0, 0.27, 0, 0.33)
		header_text1 = Ocr_Utils.perform_ocr(header_slice_image1);
		metadata_text = metadata_text + "\n" + header_text1;


		# The middle headers layout depends on layout type:
		#	In layout 1, has 2 middle headers (header 2 and 3)
		#		2: Stimulus, background, Strategy
		#		3: Pupil diameter, acuity, Rx
		#	In layout 2, has single middle header with all 6 fields

		header_text_middle = "";

		# For simiplicity, just combine all into same text string for analysi
		if (layout_version == Hvf_Object.HVF_LAYOUT_V1):

			# Header 2 slice:
			# Height: 0.0 -> 0.17
			# Width: 0.31 -> 0.547
			# Contains: Stimulus, background, and strategy
			# Recall arguments: (image, y_ratio, y_size, x_ratio, x_size)
			header_slice_image2 = Image_Utils.slice_image(hvf_image_gray, 0, 0.27, 0.31, (0.547-0.31));
			header_text2 = Ocr_Utils.perform_ocr(header_slice_image2);


			# Header 3 slice:
			# Height: 0.0 -> 0.17
			# Width: 0.52 -> 0.758 (vs 0.83 to overshoot a little given different layout low/high res) 
			# Contains: pupil diameter, visual acuity, Rx
			# Recall arguments: (image, y_ratio, y_size, x_ratio, x_size)
			header_slice_image3 = Image_Utils.slice_image(hvf_image_gray, 0, 0.27, 0.547, (0.83-0.547));
			header_text3 = Ocr_Utils.perform_ocr(header_slice_image3);

			header_text_middle = header_text2 + header_text3

		if (layout_version == Hvf_Object.HVF_LAYOUT_V2):

			# Middle Header slice:
			# Height: 0.0 -> 0.27
			# Width: 0.403 -> 0.75
			# Contains: Stimulus, background, and strategy
			# Recall arguments: (image, y_ratio, y_size, x_ratio, x_size)
			header_slice_image_middle = Image_Utils.slice_image(hvf_image_gray, 0, 0.27, 0.403, (0.75-0.403));

			header_text_middle = Ocr_Utils.perform_ocr(header_slice_image_middle);

		# Header 4 slice:
		# Height: 0.0 -> 0.17
		# Width: 0.71 -> 1.0
		# Contains: laterality, DOB, date of test, time and age

		# Recall arguments: (image, y_ratio, y_size, x_ratio, x_size)
		header_slice_image4 = Image_Utils.slice_image(hvf_image_gray, 0, 0.27, 0.71, (1.0-0.71));
		header_text4 = Ocr_Utils.perform_ocr(header_slice_image4);
		metadata_text = metadata_text + "\n" + header_text4;

		hvf_metadata = {};

		Logger.get_logger().log_msg(Logger.DEBUG_FLAG_DEBUG, "===== Extracting Metadata =====");

		# For metadata extraction, few things to consider:
		# 1. OCR is not 100% accurate, so need to use "fuzzy" matching (ie, closest fit)
		#    to maximize ability to identify specific fields
		# 2. Again OCR is not 100% accurate, so will need to clean up fields a little to
		#    make them most accurate (eg, we know laterality is either Right or Left, so
		#    make sure its one of those)
		# 3. To optimize searching, only look for metadata fields in the text slices we
		#    expect them to be in. This increases accuracy (less incorrect IDs because
		#    fewer options) and increases search speed (less things to search through)
		# 4. As we identify things (if its a sufficiently high match), we can delete them
		#    from the search list to improve next items' accuracy/speed (see above)

		# TODO: Implement ID for stimulus, etc (other header texts commented out above)

		# Tokenized list of metadata texts:
		tokenized_header1_list = header_text1.split("\n");
		tokenized_header_middle_list = header_text_middle.split("\n")
		tokenized_header4_list = header_text4.split("\n");

		tokenized_metadata_list = metadata_text.split("\n");

		#print("Header1")
		#print(str(tokenized_header1_list));

		#print("Header Middle")
		#print(str(tokenized_header_middle_list));

		#print("Header4")
		#print(str(tokenized_header4_list));

		# For each field, fuzzy regex extract metadata
		# Note that the tokenized list varies for each field depending on where it is located
		# on the page

		# Also note that function modifies the list (deletes the entry) so we have to
		# save that change

		# Because we deal with multiple layouts/versions, we may have to look for
		# metadata entries in different ways if we fail

		# ===== NAME/ID DETECTION =====
		if (layout_version == Hvf_Object.HVF_LAYOUT_V1):
			field, tokenized_header1_list = Regex_Utils.fuzzy_regex('Name: ', tokenized_header1_list);
			hvf_metadata[Hvf_Object.KEYLABEL_NAME] = field;

			field, tokenized_header1_list = Regex_Utils.fuzzy_regex('ID: ', tokenized_header1_list);
			field = Regex_Utils.remove_spaces(field);
			hvf_metadata[Hvf_Object.KEYLABEL_ID] = field;

		if (layout_version == Hvf_Object.HVF_LAYOUT_V2):
			field, tokenized_header1_list = Regex_Utils.fuzzy_regex('Patient ID: ', tokenized_header1_list);

			field = Regex_Utils.remove_spaces(field);
			hvf_metadata[Hvf_Object.KEYLABEL_ID] = field;

			field, tokenized_header1_list = Regex_Utils.fuzzy_regex('Patient: ', tokenized_header1_list);
			hvf_metadata[Hvf_Object.KEYLABEL_NAME] = field;

		# ===== DOB DETECTION =====
		if (layout_version == Hvf_Object.HVF_LAYOUT_V1):
			field, tokenized_header4_list = Regex_Utils.fuzzy_regex('DOB: ', tokenized_header4_list);
			field = Regex_Utils.remove_spaces(field);
			field = Regex_Utils.remove_non_numeric(field, ['-', '/']);

		if (layout_version == Hvf_Object.HVF_LAYOUT_V2):
			field, tokenized_header1_list = Regex_Utils.fuzzy_regex('Date of Birth:', tokenized_header1_list);

		hvf_metadata[Hvf_Object.KEYLABEL_DOB] = field;

		# ===== TEST DATE DETECTION =====

		if (layout_version == Hvf_Object.HVF_LAYOUT_V1):
			field, tokenized_header4_list = Regex_Utils.fuzzy_regex('Date: ', tokenized_header4_list);
			field = Regex_Utils.remove_spaces(field);

		if (layout_version == Hvf_Object.HVF_LAYOUT_V2):
			field, tokenized_header4_list = Regex_Utils.fuzzy_regex('Date: ', tokenized_header4_list);

		hvf_metadata[Hvf_Object.KEYLABEL_TEST_DATE] = field;

		# ===== LATERALITY DETECTION =====
		if (layout_version == Hvf_Object.HVF_LAYOUT_V1):
			field, tokenized_header4_list = Regex_Utils.fuzzy_regex('Eye: ', tokenized_header4_list);

			# We know laterality can only be 'Left' or 'Right' - fuzzy match against each to
			# produce a clean output:

			if not (field == Regex_Utils.REGEX_FAILURE):
				if (fuzz.ratio(Hvf_Object.HVF_OD, field) > fuzz.ratio(Hvf_Object.HVF_OS, field)):
					field = Hvf_Object.HVF_OD;
				else:
					field = Hvf_Object.HVF_OS;

		if (layout_version == Hvf_Object.HVF_LAYOUT_V2):
			field, tokenized_header1_list = Regex_Utils.fuzzy_regex_middle_field('| OD |', '(.*)', tokenized_header1_list);

			# We know laterality can only be 'Left' or 'Right' - fuzzy match against each to
			# produce a clean output:

			if not (field == Regex_Utils.REGEX_FAILURE):
				if (fuzz.partial_ratio("OD", field) > fuzz.partial_ratio("OS", field)):
					field = Hvf_Object.HVF_OD;
				else:
					field = Hvf_Object.HVF_OS;

		hvf_metadata[Hvf_Object.KEYLABEL_LATERALITY] = field;

		# ===== FOVEA DETECTION =====
		field, tokenized_header1_list = Regex_Utils.fuzzy_regex('Fovea:', tokenized_header1_list);

		# Detect if OFF or if value; if value, strip dB
		if not (field == Regex_Utils.REGEX_FAILURE):
			if (fuzz.partial_ratio('OFF', field) > 85):
				field = 'OFF';
			else:

				# Construct regex to fuzzy extract the value
				regexp = '(.*)\s*dB{e<=1}';

				# Perform the regex search to find the text of interest
				output = regex.search(regexp, field);

				try:
					field = output.group(1);
					field = Regex_Utils.remove_spaces(field);
				except:
					Logger.get_logger().log_msg(Logger.DEBUG_FLAG_WARNING, "Unable to extract fovea value");

		hvf_metadata[Hvf_Object.KEYLABEL_FOVEA] = field;

		# ===== RELIABILITY INDICES DETECTION =====
		field, tokenized_header1_list = Regex_Utils.fuzzy_regex('Fixation Losses: ', tokenized_header1_list);
		field = Regex_Utils.remove_spaces(field);
		field = Regex_Utils.remove_non_numeric(field, ['.', '/']);
		hvf_metadata[Hvf_Object.KEYLABEL_FIXATION_LOSS] = field;

		field, tokenized_header1_list = Regex_Utils.fuzzy_regex('False POS Errors: ', tokenized_header1_list);
		field = Regex_Utils.remove_spaces(field);
		field = field.replace("O", "0");
		hvf_metadata[Hvf_Object.KEYLABEL_FALSE_POS] = field;

		field, tokenized_header1_list = Regex_Utils.fuzzy_regex('False NEG Errors: ', tokenized_header1_list);
		field = Regex_Utils.remove_spaces(field);
		field = field.replace("O", "0");
		hvf_metadata[Hvf_Object.KEYLABEL_FALSE_NEG] = field;

		# ===== FIELD SIZE DETECTION =====
		if (layout_version == Hvf_Object.HVF_LAYOUT_V1):
			source_string_list = tokenized_header1_list
		if (layout_version == Hvf_Object.HVF_LAYOUT_V2):
			source_string_list = tokenized_header4_list

		list_of_size = [Hvf_Object.HVF_10_2, Hvf_Object.HVF_24_2, Hvf_Object.HVF_30_2];
		best_match = Regex_Utils.REGEX_FAILURE;
		best_score = 0;
		label_template_string = "Central {} Threshold Test";

		#filtered_string_list = list(filter(lambda x: len(x) >= len(label_template_string), source_string_list));
		filtered_string_list = source_string_list;
		for size in list_of_size:
			label = label_template_string.format(size);
			string_match = process.extractOne(label, filtered_string_list, scorer=fuzz.partial_ratio);

			if (string_match[1] > best_score):
				best_match = size;
				best_score = string_match[1];

		field = best_match

		hvf_metadata[Hvf_Object.KEYLABEL_FIELD_SIZE] = field;


		# ===== STRATEGY DETECTION =====
		field, tokenized_header_middle_list = Regex_Utils.fuzzy_regex('Strategy: ', tokenized_header_middle_list);

		list_of_strategies = [Hvf_Object.HVF_FULL_THRESHOLD, Hvf_Object.HVF_SITA_STANDARD, Hvf_Object.HVF_SITA_FAST]
		best_match = Regex_Utils.REGEX_FAILURE;
		best_score = 0;


		for strategy in list_of_strategies:

			score = fuzz.partial_ratio(strategy, field);

			if (score > best_score):
				best_match = strategy;
				best_score = score;

		field = best_match

		hvf_metadata[Hvf_Object.KEYLABEL_STRATEGY] = field;

		# ===== TEST DURATION DETECTION =====
		field, tokenized_header1_list = Regex_Utils.fuzzy_regex('Test Duration: ', tokenized_header1_list);
		field = Regex_Utils.remove_spaces(field);
		field = Regex_Utils.remove_non_numeric(field, [':'])
		#field = Regex_Utils.clean_nonascii(field);
		hvf_metadata[Hvf_Object.KEYLABEL_TEST_DURATION] = field;

		# ===== PUPIL DIAMETER DETECTION =====
		field, tokenized_header_middle_list = Regex_Utils.fuzzy_regex('Pupil Diameter: ', tokenized_header_middle_list);

		# Strip off everything after 'mm'
		if not (field == Regex_Utils.REGEX_FAILURE):

			# Construct regex to extract the value
			regexp = '(.*)\s*mm';

			# Perform the regex search to find the text of interest
			output = regex.search(regexp, field);

			try:
				field = output.group(1);
				field = Regex_Utils.remove_spaces(field);
			except:
				Logger.get_logger().log_msg(Logger.DEBUG_FLAG_WARNING, "Unable to extract pupil diameter");



		#field = Regex_Utils.remove_non_numeric(field, ['.'])
		hvf_metadata[Hvf_Object.KEYLABEL_PUPIL_DIAMETER] = field;

		# ===== RX DETECTION =====
		field, tokenized_header_middle_list = Regex_Utils.fuzzy_regex('Rx:', tokenized_header_middle_list);

		# If V1 layout, need to clean up:

		if (layout_version == Hvf_Object.HVF_LAYOUT_V1) and not (field == Regex_Utils.REGEX_FAILURE):
			# Construct regex to extract the value
			#print("Prelim rx: " + field)
			regexp = '(.*)[DO]S (.*)[DO0]C [XxK]*\s*(\d*){e<=1}';

			# Perform the regex search to find the text of interest
			output = regex.search(regexp, field);

			try:

				sphere = output.group(1);
				sphere = Regex_Utils.remove_spaces(sphere);
				sphere = Regex_Utils.clean_punctuation_to_period(sphere);
				sphere = Regex_Utils.remove_non_numeric(sphere, ['.', '+', '-']);

				cyl = output.group(2);
				cyl = Regex_Utils.remove_spaces(cyl);
				cyl = Regex_Utils.clean_punctuation_to_period(cyl);
				cyl = Regex_Utils.remove_non_numeric(cyl, ['.', '+', '-']);

				axis = output.group(3);
				axis = Regex_Utils.remove_spaces(axis);
				axis = Regex_Utils.remove_non_numeric(axis, []);

				# Construct our final field. To standardize formatting/minimize
				# extra spaces, construct as an array and join:

				rx_array = [];

				if (sphere):
					rx_array.append(sphere);

				rx_array.append("DS");
				if (cyl):
					rx_array.append(cyl);

				rx_array.append("DC");
				rx_array.append("X");

				if (axis):
						rx_array.append(axis);

				field = " ".join(rx_array);

			except:
				Logger.get_logger().log_msg(Logger.DEBUG_FLAG_WARNING, "Unable to extract Rx data");

		#field = Regex_Utils.remove_non_numeric(field, ['.'])
		hvf_metadata[Hvf_Object.KEYLABEL_RX] = field;

		Logger.get_logger().log_msg(Logger.DEBUG_FLAG_DEBUG, "===== End Extracting Metadata =====");

		# Lastly, return the dictionary with the metadata:
		return hvf_metadata;


	###############################################################################
	# Reads MD/PSD/VFI metadata from HVF image:
	@staticmethod
	def get_metric_metadata_from_hvf_image(hvf_image_gray, layout_version, field_size):

		# Image processing for optimization:
		# First, convert grayscale -> black and white, to optimize text detection
		hvf_image_gray = cv2.bitwise_not(cv2.adaptiveThreshold(hvf_image_gray,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY_INV,11,5));


		# Slice+OCR bottom right
		# Contains: MD, PSD, VFI
		# These ratio values are all found empirically - edit to be as narrow as possible while
		# still retaining flexibility

		# Recall arguments: (image, y_ratio, y_size, x_ratio, x_size)
		dev_val_slice_image = Image_Utils.slice_image(hvf_image_gray, 0.5, 0.15, 0.65, 0.35)
		dev_val_slice_text = Ocr_Utils.perform_ocr(dev_val_slice_image)
		tokenized_dev_val_list = dev_val_slice_text.split("\n");

		metric_metadata = {}

		# ===== MD/PSD/VFI DETECTION =====
		if (layout_version == Hvf_Object.HVF_LAYOUT_V1):
			field, tokenized_dev_val_list = Regex_Utils.fuzzy_regex_middle_field('MD dB', 'MD\s*(.*)dB{e<=2}', tokenized_dev_val_list);

		if (layout_version == Hvf_Object.HVF_LAYOUT_V2):

			# Can either be MD<FIELD SIZE> (eg, MD24-2) or MD; regex for optional
			label = 'MD{} dB'.format(field_size)
			regex_string = 'MD(?:'+field_size+')?:\s*(.*)dB{e<=2}';
			field, tokenized_dev_val_list = Regex_Utils.fuzzy_regex_middle_field(label, regex_string, tokenized_dev_val_list);

		field = Regex_Utils.clean_punctuation_to_period(field);
		field = Regex_Utils.remove_spaces(field);
		field = Regex_Utils.clean_minus_sign(field);
		field = Regex_Utils.remove_non_numeric(field, ['.', '-']);
		field = Regex_Utils.add_decimal_if_absent(field);

		metric_metadata[Hvf_Object.KEYLABEL_MD] = field;

		if (layout_version == Hvf_Object.HVF_LAYOUT_V1):
			field, tokenized_dev_val_list = Regex_Utils.fuzzy_regex_middle_field('PSD dB', 'PSD\s*(.*)dB{e<=2}', tokenized_dev_val_list);

		if (layout_version == Hvf_Object.HVF_LAYOUT_V2):

			# Can either be PSD<FIELD SIZE> (eg, PSD24-2) or PSD; regex for optional
			label = 'PSD{} dB'.format(field_size)
			regex_string = 'PSD(?:'+field_size+')?:\s*(.*)dB{e<=2}';
			field, tokenized_dev_val_list = Regex_Utils.fuzzy_regex_middle_field(label, regex_string, tokenized_dev_val_list);

		field = Regex_Utils.clean_punctuation_to_period(field);
		field = Regex_Utils.remove_spaces(field);
		field = Regex_Utils.add_decimal_if_absent(field);

		metric_metadata[Hvf_Object.KEYLABEL_PSD] = field;

		if (layout_version == Hvf_Object.HVF_LAYOUT_V1):
			field, tokenized_dev_val_list = Regex_Utils.fuzzy_regex_middle_field('VFI', 'VFI\s*(.*)%{e<=2}', tokenized_dev_val_list);

		if (layout_version == Hvf_Object.HVF_LAYOUT_V2):
			field, tokenized_dev_val_list = Regex_Utils.fuzzy_regex('VFI: ', tokenized_dev_val_list);
			#field, tokenized_dev_val_list = Regex_Utils.fuzzy_regex_middle_field('VFI', 'VFI:\s*(.*)%{e<=2}', tokenized_dev_val_list);

		field = Regex_Utils.clean_punctuation_to_period(field);
		field = Regex_Utils.remove_spaces(field);
		metric_metadata[Hvf_Object.KEYLABEL_VFI] = field;


		return metric_metadata;

	###############################################################################
	# Validates field size/laterality from argument plot:
	def get_field_size_laterality_from_plot(val_plot):

		dict = {};

		field_testing = {
			Hvf_Object.HVF_24_2: Hvf_Plot_Array.BOOLEAN_MASK_24_2,
			Hvf_Object.HVF_10_2: Hvf_Plot_Array.BOOLEAN_MASK_10_2,
			Hvf_Object.HVF_30_2: Hvf_Plot_Array.BOOLEAN_MASK_30_2,

		};

		laterality_testing = [Hvf_Object.HVF_OD, Hvf_Object.HVF_OS]

		for field in field_testing:
			boolean_mask_plot = field_testing[field];

			for laterality in laterality_testing:

				if (Hvf_Object.compare_plot_template(val_plot, boolean_mask_plot, laterality)):
					dict[Hvf_Object.KEYLABEL_FIELD_SIZE] = field;

					if not (field == Hvf_Object.HVF_10_2):
						dict[Hvf_Object.KEYLABEL_LATERALITY] = laterality;

					return dict;

		return dict;

	###############################################################################
	# Helper function for validating field size/laterality
	def compare_plot_template(val_plot, boolean_mask_plot, laterality):

		if (laterality == Hvf_Object.HVF_OD):
			laterality_conversion = 0;
		else:
			laterality_conversion = 9;

		for c in range(0, 10):
			for r in range(0, 10):

				val = np.asscalar(val_plot.get_plot_array()[c, r]);

				boolean = boolean_mask_plot[r][abs(c-laterality_conversion)];

				# If boolean mask expects null element and we don't have VALUE_NO_VALUE, return false
				if ((boolean == 0) and not (val.get_value() == Hvf_Value.VALUE_NO_VALUE)):
					return False;

		return True;

	###############################################################################
	# PLOT EXTRACTION METHODS #####################################################
	###############################################################################

	###############################################################################
	# Get absolute raw value plot:
	@staticmethod
	def get_abs_raw_val_plot(hvf_image_gray):
		# Slice, then call a common func 'get_plot'

		# Slice out percentile pattern deviation plot:
		# Recall arguments: (image, y_ratio, y_size, x_ratio, x_size)
		# These ratios are all found empirically from the HVF printout
		# Height: 0.16 -> 0.49
		# Width: 0.14 -> 0.58
		y_ratio = 0.16;
		y_size = 0.33;
		x_ratio = 0.14;
		x_size = 0.44;

		plot_type = Hvf_Plot_Array.PLOT_RAW;
		icon_type = Hvf_Plot_Array.PLOT_VALUE;

		Logger.get_logger().log_msg(Logger.DEBUG_FLAG_INFO, "Extracting Absolute Raw Value Plot");


		# Use common function for all plots - specify we anticipate this to be a value
		# icon plot
		return Hvf_Plot_Array.get_plot_from_image(hvf_image_gray, plot_type, icon_type, y_ratio, y_size, x_ratio, x_size);


	###############################################################################
	# Get absolute deviation value plot:
	@staticmethod
	def get_abs_deviation_val_plot(hvf_image_gray):
		# Slice, then call a common func 'get_plot'

		# Slice out percentile pattern deviation plot:
		# Recall arguments: (image, y_ratio, y_size, x_ratio, x_size)
		# These ratios are all found empirically from the HVF printout
		# Height: 0.4 -> 0.6
		# Width: 0.0 -> 0.40
		y_ratio = 0.4;
		y_size = 0.30;
		x_ratio = 0.0;
		x_size = 0.4;

		plot_type = Hvf_Plot_Array.PLOT_TOTAL_DEV;
		icon_type = Hvf_Plot_Array.PLOT_VALUE;

		Logger.get_logger().log_msg(Logger.DEBUG_FLAG_INFO, "Extracting Absolute Deviation Value Plot");

		# Use common function for all plots - specify we anticipate this to be a value
		# icon plot
		return Hvf_Plot_Array.get_plot_from_image(hvf_image_gray, plot_type, icon_type, y_ratio, y_size, x_ratio, x_size);

	###############################################################################
	# Get pattern deviation value plot:
	@staticmethod
	def get_pattern_deviation_val_plot(hvf_image_gray):
		# Slice, then call a common func 'get_plot'

		# Slice out percentile pattern deviation plot:
		# Recall arguments: (image, y_ratio, y_size, x_ratio, x_size)
		# These ratios are all found empirically from the HVF printout
		# Height: 0.4 -> 0.6
		# Width: 0.35 -> 0.75
		y_ratio = 0.4;
		y_size = 0.30;
		x_ratio = 0.35;
		x_size = 0.4;

		plot_type = Hvf_Plot_Array.PLOT_PATTERN_DEV;
		icon_type = Hvf_Plot_Array.PLOT_VALUE;

		Logger.get_logger().log_msg(Logger.DEBUG_FLAG_INFO, "Extracting Pattern Deviation Value Plot");

		# Use common function for all plots - specify we anticipate this to be a value
		# icon plot
		return Hvf_Plot_Array.get_plot_from_image(hvf_image_gray, plot_type, icon_type, y_ratio, y_size, x_ratio, x_size);


	###############################################################################
	# Get absolute deviation percentile plot:
	@staticmethod
	def get_abs_deviation_perc_plot(hvf_image_gray):
		# Slice, then call a common func 'get_plot'

		# Slice out absolute pattern deviation plot:
		# Recall arguments: (image, y_ratio, y_size, x_ratio, x_size)
		# These ratios are all found empirically from the HVF printout
		# Height: 0.60 -> 0.9 (these are wide margins to allow for flexibility)
		# Width: 0.0 -> 0.40
		y_ratio = 0.6;
		y_size = 0.30;
		x_ratio = 0.0;
		x_size = 0.4;

		plot_type = Hvf_Plot_Array.PLOT_TOTAL_DEV;
		icon_type = Hvf_Plot_Array.PLOT_PERC;

		Logger.get_logger().log_msg(Logger.DEBUG_FLAG_INFO, "Extracting Absolute Deviation Percentile Plot");

		# Use common function for all plots - specify we anticipate this to be a percentile
		# icon plot
		return Hvf_Plot_Array.get_plot_from_image(hvf_image_gray, plot_type, icon_type, y_ratio, y_size, x_ratio, x_size);



	###############################################################################
	# Get pattern deviation percentile plot:
	@staticmethod
	def get_pattern_deviation_perc_plot(hvf_image_gray):
		# Slice, then call a common func 'get_plot'

		# Slice out percentile pattern deviation plot:
		# Recall arguments: (image, y_ratio, y_size, x_ratio, x_size)
		# These ratios are all found empirically from the HVF printout
		# Height: 0.6 -> 0.9
		# Width: 0.35 -> 0.75
		y_ratio = 0.6;
		y_size = 0.30;
		x_ratio = 0.35;
		x_size = 0.4;

		plot_type = Hvf_Plot_Array.PLOT_PATTERN_DEV;
		icon_type = Hvf_Plot_Array.PLOT_PERC;

		Logger.get_logger().log_msg(Logger.DEBUG_FLAG_INFO, "Extracting Pattern Deviation Percentile Plot");

		# Use common function for all plots - specify we anticipate this to be a percentile
		# icon plot
		return Hvf_Plot_Array.get_plot_from_image(hvf_image_gray, plot_type, icon_type, y_ratio, y_size, x_ratio, x_size);
