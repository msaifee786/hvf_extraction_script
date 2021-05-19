###############################################################################
# hvf_value.py - OCR VERSION
#
# Description:
#	Class definition for a HVF value icon/number detector HVF object. Meant to
#	beused in the hvf_object class as a helper class.
#
#	Uses OpenCV image detection/template matching to match value number icons
#	from a list of known icons.
#
# Main usage:
#	Call init method to initialize all reference icons
#
#	Call factory with image corresponding to cell (or enum) to identify. Performs
#	2 major tasks:
#		1. Icon detection/cropping
#		2. Icon recognition
#
#	To Do:
#		- Get display string
#
#
###############################################################################

# Import necessary packages
import cv2
import sys
import os

# Import some helper packages:
import numpy as np
from PIL import Image
from functools import reduce

import pkgutil
import random

# Import some of our own written modules:

# For error/debug logging:
from hvf_extraction_script.utilities.logger import Logger

# General purpose image functions:
from hvf_extraction_script.utilities.image_utils import Image_Utils

# For reading files:
from hvf_extraction_script.utilities.file_utils import File_Utils

class Hvf_Value:

	###############################################################################
	# CONSTANTS AND STATIC VARIABLES ##############################################
	###############################################################################

	###############################################################################
	# Value/Percentile icons and enums

	# Value enum corresponding to blank:
	VALUE_NO_VALUE = -99;
	VALUE_FAILURE = -98;
	VALUE_BELOW_THRESHOLD = -97;

	VALUE_NO_VALUE_CHAR = " ";
	VALUE_FAILURE_CHAR = "?";
	VALUE_BELOW_THRESHOLD_CHAR = "<0";


	VALUE_MAX_VALUE = 50
	VALUE_MIN_VALUE_RAW = 0
	VALUE_MIN_VALUE_DEV = -50

	# Class variables:
	# Need icon templates for value digits to match against:
	value_0_template = None;
	value_1_template = None;
	value_2_template = None;
	value_3_template = None;
	value_4_template = None;
	value_5_template = None;
	value_6_template = None;
	value_7_template = None;
	value_8_template = None;
	value_9_template = None;

	value_minus_template = None;

	value_less_than_template = None;

	template_value_list = None;

	# Initialization flag
	is_initialized = False;

	###############################################################################
	# CONSTRUCTOR AND FACTORY METHODS #############################################
	###############################################################################

	###############################################################################
	# Initializer method
	# Not to be used publicly - use factory methods instead
	# Takes in pertinent data (enum corresponding to percentile icon, and image
	# slice)
	def __init__(self, value, image_slice):

		self.value = value;
		self.raw_image = image_slice;

	###############################################################################
	# Factory method - given an image slice, returns a value corresponding to the
	# image
	@staticmethod
	def get_value_from_image(slice, slice_backup, plot_type):


		value = Hvf_Value.get_value_plot_element(slice, slice_backup, plot_type);

		exception_list = [Hvf_Value.VALUE_FAILURE, Hvf_Value.VALUE_NO_VALUE, Hvf_Value.VALUE_BELOW_THRESHOLD ]

		# In case value generated is incorrect, bring within normal limits:
		if not (value in exception_list):
			if (value > Hvf_Value.VALUE_MAX_VALUE):
				value = Hvf_Value.VALUE_MAX_VALUE;

			elif ((plot_type == 'raw') and (value < Hvf_Value.VALUE_MIN_VALUE_RAW)):

				value = Hvf_Value.VALUE_MIN_VALUE_RAW

			elif (not (plot_type == 'raw') and (value < Hvf_Value.VALUE_MIN_VALUE_DEV)):

				value = Hvf_Value.VALUE_MIN_VALUE_DEV

		return Hvf_Value(value, slice);

	###############################################################################
	# Factory method - given an number, returns a value corresponding to the
	# cell (used for deserialization)
	@staticmethod
	def get_value_from_display_string(num):

		if (num == "" or num == " "):
			num = Hvf_Value.VALUE_NO_VALUE;
		elif (num == Hvf_Value.VALUE_FAILURE_CHAR):
			num = Hvf_Value.VALUE_FAILURE;
		elif (num == Hvf_Value.VALUE_BELOW_THRESHOLD_CHAR):
			num = Hvf_Value.VALUE_BELOW_THRESHOLD;
		else:
			try:
				num = int(num);
			except:
				num = Hvf_Value.VALUE_FAILURE

		return Hvf_Value(num, None);


	###############################################################################
	# INITIALIZATION METHODS ######################################################
	###############################################################################

	###############################################################################
	# Variable Initialization method - does some preprocessing for variables for
	# ease of calculation
	@classmethod
	def initialize_class_vars(cls):

		# Load all the icon images for matching:

		# Declare our template dictionaries:
		cls.value_icon_templates = {};
		cls.minus_icon_templates = {};
		cls.less_than_icon_templates = {};

		# Iterate through the icon folders:

		module_list = ["hvf_extraction_script.hvf_data.value_icons.v0", "hvf_extraction_script.hvf_data.value_icons.v1", "hvf_extraction_script.hvf_data.value_icons.v2"]

		for module in module_list:

			module_dir, _ = os.path.split(pkgutil.get_loader(module).get_filename());

			head, dir  = os.path.split(module_dir);

			# Assume that names are standardized within the directory:

			# Add number value icons (construct file names):

			for ii in range(10):
				# Construct filename:
				value_icon_file_name = 'value_' + str(ii) + '.PNG';

				# Construct full path:
				value_icon_full_path = os.path.join(module_dir, value_icon_file_name);
				icon_template = cv2.cvtColor(File_Utils.read_image_from_file(value_icon_full_path), cv2.COLOR_BGR2GRAY);

				# Add to value icon template dictionary:
				if not (ii in cls.value_icon_templates):
					cls.value_icon_templates[ii] = {};

				cls.value_icon_templates[ii][dir] = icon_template;


			# Add minus template:
			minus_icon_full_path = os.path.join(module_dir, 'value_minus.PNG')
			minus_template = cv2.cvtColor(File_Utils.read_image_from_file(minus_icon_full_path), cv2.COLOR_BGR2GRAY);

			cls.minus_icon_templates[dir] = minus_template;

			# Add less than template:
			less_than_full_path = os.path.join(module_dir, 'value_less_than.PNG')
			less_than_template = cv2.cvtColor(File_Utils.read_image_from_file(less_than_full_path), cv2.COLOR_BGR2GRAY);

			cls.less_than_icon_templates[dir] = less_than_template;

		# Lastly, flip the flag to indicate initialization has been done
		cls.is_initialized = True;

		return None;


	###############################################################################
	# OBJECT METHODS ##############################################################
	###############################################################################

	###############################################################################
	# Simple accessor for value (NOTE: May be other enum - NO_VALUE or FAILURE)
	def get_value(self):
		return self.value;

	###############################################################################
	# Simple accessor for image (NOTE: may be None)
	def get_source_image(self):
		return self.raw_image;

	###############################################################################
	# Simple accessor/toString method
	def get_display_string(self):
		return Hvf_Value.get_string_from_value(self.value);


	###############################################################################
	# Simple accessor/toString method
	def get_standard_size_display_string(self):

		x = self.get_display_string();

		# Otherwise return standardized size:
		if (len(x) == 1):
			x = "  "+x;
		elif (len(x) == 2):
			x = " "+x
		elif (len(x) == 3):
			x = x;

		return x;

	###############################################################################
	# Simple equals method
	def is_equal(self, other):
		return (isinstance(other, Hvf_Value) and (self.get_value() == other.get_value()));

	###############################################################################
	# Releases saved images (to help save memory)
	def release_saved_image(self):

		self.raw_image = None;

		return;

	###############################################################################
	# HELPER METHODS ##############################################################
	###############################################################################

	###############################################################################
	# Helper method for value -> display string
	def get_string_from_value(value):
		# Determine if we have any special chars;
		if (value == Hvf_Value.VALUE_NO_VALUE):
			x = Hvf_Value.VALUE_NO_VALUE_CHAR;
		elif (value == Hvf_Value.VALUE_FAILURE):
			x = Hvf_Value.VALUE_FAILURE_CHAR;
		elif (value == Hvf_Value.VALUE_BELOW_THRESHOLD):
			x = Hvf_Value.VALUE_BELOW_THRESHOLD_CHAR;
		else:
			x = str(value);

		return x;


	def contour_bound_box_area(x):
		x,y,w,h = cv2.boundingRect(x);
		return w*h;

	def contour_x_dim(x):
		x,y,w,h = cv2.boundingRect(x);
		return x;

	def contour_width(c):
		x,y,w,h = cv2.boundingRect(c);
		return w;

	###############################################################################
	# Given a plot element, finds number of contours
	@staticmethod
	def find_num_contours(plot_element):

		plot_element_temp = cv2.bitwise_not(plot_element.copy());
		cnts, hierarchy = cv2.findContours(plot_element_temp, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

		return len(cnts);

	###############################################################################
	# Given an image slice, cleans it up (preparing for digit value detection):
	@staticmethod
	def clean_slice(slice):

		# Clean up borders - sometimes straggler pixels come along
		slice_w = np.size(slice, 1);

		slice = slice[:,1:slice_w-1];
		slice = cv2.copyMakeBorder(slice,0,0,1,1,cv2.BORDER_REPLICATE);

		# Crop the characters to remove excess white:
		x0, x1, y0, y1 = Image_Utils.crop_white_border(slice);

		# Possible we have a fully blank slice, so only crop if there is something
		if (x0 < x1 and y0 < y1):
			slice = slice[y0:y1, x0:x1];

		return slice;


	###############################################################################
	# Given an image slice, chops number and returns a list of separate digits slices
	def chop_into_char_list(slice):

		# W/H Ratio for character
		MAX_W_H_RATIO = 0.7

		ret_list = [];

		slice_h = np.size(slice, 0);

		# Get contours:
		slice_temp = cv2.bitwise_not(slice);
		cnts, hierarchy = cv2.findContours(slice_temp, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

		# Sort contours from left to right
		cnts = sorted(cnts, key = Hvf_Value.contour_x_dim);

		# Iterate through the contours:
		for ii in range(len(cnts)):

			# Get bounding box:
			x,y,w,h = cv2.boundingRect(cnts[ii]);

			# The contour may contain multiple digits, so need to detect it:
			if (w/slice_h > MAX_W_H_RATIO):
				Logger.get_logger().log_msg(Logger.DEBUG_FLAG_DEBUG, "Multiple Digits");

				DIGIT_WH_RATIO = 0.575;

				# Multiple digits
				expected_num_chars = max(round(((w/slice_h)/DIGIT_WH_RATIO)+0.15), 1);


				for ii in range(expected_num_chars):
					x_coor = x+(int(w*ii/expected_num_chars));
					x_size = int(w/expected_num_chars);

					# Slice them:
					char_slice = slice[:, x_coor:x_coor+x_size];

					# And append slice to list:
					ret_list.append(char_slice);

			else:
				char_slice = slice[:, x:x+w];

				ret_list.append(char_slice);

		Logger.get_logger().log_msg(Logger.DEBUG_FLAG_DEBUG, "Showing Element " + str(Hvf_Value.i));
		Logger.get_logger().log_msg(Logger.DEBUG_FLAG_DEBUG, "Number of elements: " + str(len(ret_list)));
		for ii in range(len(ret_list)):
			show_element_func = (lambda : cv2.imshow('Element ' + str(Hvf_Value.i) +'.'+ str(ii), ret_list[ii]))
			Logger.get_logger().log_function(Logger.DEBUG_FLAG_DEBUG, show_element_func);
		return ret_list;


	###############################################################################
	# Given an image and a icon template, scales the icon to the height of the image
	# and copyBorders the image to match the sizes. Then, performs template matching
	# and returns the result
	@staticmethod
	def resize_and_template_match(image, icon):

		h = np.size(image, 0);

		# Scale the value icon:
		scale_factor = h/np.size(icon, 0)

		icon = cv2.resize(icon, (0,0), fx=scale_factor, fy=scale_factor);

		# In case the original is too small by width compared to icon, need to widen;
		# do so by copymakeborder replicate
		image = image.copy();

		if (np.size(image, 1) < np.size(icon, 1)):
			border = np.size(icon, 1) - np.size(image, 1);
			image = cv2.copyMakeBorder(image,0,0,0,border,cv2.BORDER_REPLICATE);

		# Apply template matching:
		temp_matching = cv2.matchTemplate(image, icon, cv2.TM_CCOEFF_NORMED)

		# Grab our result
		min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(temp_matching);

		return max_val;

	###############################################################################
	# Helper function: Given a image, determines if it is a "<" sign - returns
	# boolean
	# Uses template matching
	@staticmethod
	def is_less_than(plot_element):

		LESS_THAN_DETECTION_THRESHOLD = 0.4;

		best_match_val = 0;

		for key in Hvf_Value.less_than_icon_templates:

			match_val = Hvf_Value.resize_and_template_match(plot_element, Hvf_Value.less_than_icon_templates[key]);

			best_match_val = max(match_val, best_match_val);

		# Return if either match value worked:
		return best_match_val > LESS_THAN_DETECTION_THRESHOLD


	###############################################################################
	# Helper function: Given a image, determines if it is a "-" sign - returns
	# boolean
	# Uses template matching
	@staticmethod
	def is_minus(plot_element):

		THRESHOLD_MATCH_MINUS = 0.55;

		best_match_val = 0;

		for key in Hvf_Value.minus_icon_templates:

			match_val = Hvf_Value.resize_and_template_match(plot_element, Hvf_Value.minus_icon_templates[key]);

			best_match_val = max(match_val, best_match_val);

		# Return if either match value worked:
		return best_match_val > THRESHOLD_MATCH_MINUS

	###############################################################################
	# Helper function: Given an image of a single digit, returns the best match
	# Uses template matching
	@staticmethod
	def identify_digit(plot_element, allow_search_zero):

		# We template match against all icons and look for best fit:
		best_match = None
		best_val = None;
		best_loc = None;
		best_scale_factor = None;
		best_dir = None;

		height = np.size(plot_element, 0)
		width = np.size(plot_element, 1)

		# Can skip 0 if flag tells us to. This can help maximize accuracy in low-res cases
		# Do this when we know something about the digit (it is a leading digit, etc)
		start_index = 0;
		if not allow_search_zero:
			start_index = 1;


		for ii in range(start_index, len(Hvf_Value.value_icon_templates.keys())):

			for dir in Hvf_Value.value_icon_templates[ii]:


				# First, scale our template value:
				val_icon = Hvf_Value.value_icon_templates[ii][dir];

				plot_element_temp = plot_element.copy();

				scale_factor = 1;
				# Use the smaller factor to make sure we fit into the element icon
				if (height < np.size(val_icon, 0)):
					# Need to upscale plot_element
					scale_factor = np.size(val_icon, 0)/height;
					plot_element_temp = cv2.resize(plot_element_temp, (0,0), fx=scale_factor, fy=scale_factor)

				else:
					# Need to upscale val_icon
					scale_factor = height/(np.size(val_icon, 0));
					val_icon = cv2.resize(val_icon, (0,0), fx=scale_factor, fy=scale_factor);


				# In case the original is too small by width compared to value_icon, need
				# to widen - do so by copymakeborder replicate

				if (np.size(plot_element_temp, 1) < np.size(val_icon, 1)):
					border = np.size(val_icon, 1) - np.size(plot_element_temp, 1);
					#plot_element_temp = cv2.copyMakeBorder(plot_element_temp,0,0,0,border,cv2.BORDER_CONSTANT,0);

				# Apply template matching:
				temp_matching = cv2.matchTemplate(plot_element_temp, val_icon, cv2.TM_CCOEFF_NORMED)

				# Grab our result
				min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(temp_matching);

				Logger.get_logger().log_msg(Logger.DEBUG_FLAG_DEBUG, "Matching against " + str(ii) + ": " + str(max_val));

				# Check to see if this is our best fit yet:
				if (best_match is None or max_val > best_match):
					# This is best fit - record the match value and the actual value
					best_match = max_val;
					best_val = ii;
					best_loc = max_loc;
					best_scale_factor = scale_factor;
					best_dir = dir;
		# TODO: refine specific cases that tend to be misclassified

		# 1 vs 4
		if (best_val == 4 or best_val == 1):

			if (best_dir == "v0"):

				# Cut number in half and take bottom half -> find contours
				# If width of contour is most of element --> 4
				# otherwise, 1

				bottom_half = Image_Utils.slice_image(plot_element, 0.50, 0.25, 0, 1);

				cnts, hierarchy = cv2.findContours(cv2.bitwise_not(bottom_half.copy()), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

				# Sort contours by width
				sorted_contours = sorted(cnts, key = Hvf_Value.contour_width, reverse = True)
				#largest_contour = sorted(cnts, key = Hvf_Value.contour_width, reverse = True)[0];

				if (len(sorted_contours) > 0):

					if (Hvf_Value.contour_width(sorted_contours[0]) > width*0.8):
						best_val = 4;
					else:
						best_val = 1;

			if ((best_dir == "v1") or (best_dir == "v2")):
				# Cut number in half and take bottom half -> find contours
				# If width of contour is most of element --> 4
				# otherwise, 1

				bottom_half = Image_Utils.slice_image(plot_element, 0.50, 0.50, 0, 1);

				cnts, hierarchy = cv2.findContours(cv2.bitwise_not(bottom_half.copy()), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

				# Sort contours by width
				sorted_contours = sorted(cnts, key = Hvf_Value.contour_width, reverse = True)
				#largest_contour = sorted(cnts, key = Hvf_Value.contour_width, reverse = True)[0];

				if (len(sorted_contours) > 0):

					if (Hvf_Value.contour_width(sorted_contours[0]) > width*0.8):
						best_val = 4;
					else:
						best_val = 1;

		Logger.get_logger().log_msg(Logger.DEBUG_FLAG_DEBUG, "Best match {}, best dir {}".format(best_val, best_dir));

		return best_val, best_loc, best_scale_factor, best_match;

	###############################################################################
	# RAW VALUE IDENTIFICATION VERSION: ###########################################
	###############################################################################

	###############################################################################
	# Get the corresponding value element/number from the plot element:
	@staticmethod
	def get_value_plot_element(plot_element, plot_element_backup, plot_type):
		# Declare return value
		return_val = 0;

		# CV2 just slices images and returns the native image. We mess with the pixels so
		# for cleanliness, just copy it over:
		plot_element = plot_element.copy();

		# First, clean up any small noisy pixels by eliminating small contours
		# Tolerance for stray marks is different depending on plot type


		# Relative to largest contour:
		plot_threshold = 0
		relative_threshold = 0

		if (plot_type == "raw"):
			plot_threshold = 0.005
			relative_threshold = 0.1
		else:
			plot_threshold = 0.005
			relative_threshold = 0.01

		plot_element = Image_Utils.delete_stray_marks(plot_element, plot_threshold, relative_threshold)
		plot_element_backup = Image_Utils.delete_stray_marks(plot_element_backup, plot_threshold, relative_threshold)

		# Now, crop out the borders so we just have the central values - this allows us
		# to standardize size
		x0, x1, y0, y1 = Image_Utils.crop_white_border(plot_element);

		# Now we have bounding x/y coordinates
		# Calculate height and width:
		h = y1 - y0;
		w = x1 - x0

		# Sometimes in low quality images, empty cells may have noise - also need to filter
		# based on area of element
		#THRESHOLD_AREA_FRACTION = 0.03;
		#fraction_element_area = (w*h)/(np.size(plot_element, 0)*np.size(plot_element, 1));

		# If this was an empty plot, (or element area is below threshold) we have no value
		#if ((w <= 0) or (h <= 0) or fraction_element_area < THRESHOLD_AREA_FRACTION):
		if (w <= 0) or (h <= 0):
			Logger.get_logger().log_msg(Logger.DEBUG_FLAG_DEBUG, "Declaring no value because cell is empty/below threshold marks");

			return_val = Hvf_Value.VALUE_NO_VALUE;

			Hvf_Value.i = Hvf_Value.i+1;
		else:


			# First, split the slice into a character list:

			list_of_chars = Hvf_Value.chop_into_char_list(plot_element[y0:1+y1,x0:1+x1]);
			list_of_chars_backup = Hvf_Value.chop_into_char_list(plot_element[y0:1+y1,x0:1+x1]);


			# Check for special cases (ie, non-numeric characters)

			# Check if <0 value
			# Can optimize detection accuracy by limiting check to only raw plot values with 2 chars:
			if (plot_type == "raw" and len(list_of_chars) == 2 and (Hvf_Value.is_less_than(list_of_chars[0]) or Hvf_Value.is_less_than(list_of_chars_backup[0]))):

				Logger.get_logger().log_msg(Logger.DEBUG_FLAG_DEBUG, "Detected less-than sign");
				return_val = Hvf_Value.VALUE_BELOW_THRESHOLD;

			# Check if the above detection worked:
			if (return_val == 0):

				# No, so continue detection for number

				# Determine if we have a minus sign
				is_minus = 1;

				# First, look for minus sign - if we have 2 or 3 characters

				# Negative numbers are not present in raw plot
				if not (plot_type == "raw"):

					if (len(list_of_chars) == 2 and Hvf_Value.is_minus(list_of_chars[0])):

						# Detected minus sign:
						Logger.get_logger().log_msg(Logger.DEBUG_FLAG_DEBUG, "Detected minus sign");

						# Set our multiplier factor (makes later numeric correction easier)
						is_minus = -1;

						# Remove the character from the list
						list_of_chars.pop(0);
						list_of_chars_backup.pop(0);

					elif (len(list_of_chars) == 3):
						# We know there must be a minus sign, so just raise flag
						Logger.get_logger().log_msg(Logger.DEBUG_FLAG_DEBUG, "Assuming minus sign");

						is_minus = -1;
						# Remove the character from the list
						list_of_chars.pop(0);
						list_of_chars_backup.pop(0);

				# Now, look for digits, and calculate running value

				running_value = 0;

				for jj in range(len(list_of_chars)):


					# Pull out our digit to detect, and clean it
					digit = Hvf_Value.clean_slice(list_of_chars[jj]);

					show_element_func = (lambda : cv2.imshow('Sub element ' + str(Hvf_Value.i) + "_"+ str(jj), digit))
					Logger.get_logger().log_function(Logger.DEBUG_FLAG_DEBUG, show_element_func);

					Hvf_Value.j = Hvf_Value.j + 1;

					# Search for 0 if it is the trailing 0 of a multi-digit number, or if lone digit and not a minus
					allow_search_zero = ((jj == len(list_of_chars)-1) and (len(list_of_chars) > 1)) or ((len(list_of_chars) == 1) and (is_minus == 1));

					Logger.get_logger().log_msg(Logger.DEBUG_FLAG_DEBUG, "Allow 0 search: " + str(allow_search_zero));
					Logger.get_logger().log_msg(Logger.DEBUG_FLAG_DEBUG, "jj: " + str(jj));
					Logger.get_logger().log_msg(Logger.DEBUG_FLAG_DEBUG, "list_of_chars length: " + str(len(list_of_chars)));

					best_value, best_loc, best_scale_factor, best_match = Hvf_Value.identify_digit(digit, allow_search_zero);


					# If not a good match, recheck with alternatively processed image -> may increase yield
					threshold_match_digit = 0.5

					if (best_match > 0 and best_match < threshold_match_digit):

						digit_backup = Hvf_Value.clean_slice(list_of_chars_backup[jj]);
						best_value, best_loc, best_scale_factor, best_match = Hvf_Value.identify_digit(digit_backup, allow_search_zero);

					running_value = (10*running_value)+best_value;


				Hvf_Value.i = Hvf_Value.i+1;
				Hvf_Value.j = 0;

				return_val = running_value*is_minus;

		# Debug info string for the best matched value:
		debug_best_match_string = "Best matched value: " + Hvf_Value.get_string_from_value(return_val);
		Logger.get_logger().log_msg(Logger.DEBUG_FLAG_INFO, debug_best_match_string);

		return return_val;



	i = 0
	j = 0;
