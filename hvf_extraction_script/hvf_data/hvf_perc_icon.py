###############################################################################
# hvf_perc_icon.py
#
# Description:
#	Class definition for a HVF percentile icon detector HVF object. Meant to be
#	used in the hvf_object class as a helper class.
#
#	Uses OpenCV image detection/template matching to match percentile icons from
#	a list of known icons.
#
# Main usage:
#	Call init method to initialize all reference icons
#
#	Call factory with image (or enum) corresponding to cell to identify. Performs 2
#	major tasks:
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

# Import some of our own written modules:
from hvf_extraction_script.utilities.logger import Logger
from hvf_extraction_script.utilities.image_utils import Image_Utils
from hvf_extraction_script.utilities.file_utils import File_Utils

class Hvf_Perc_Icon:

	###############################################################################
	# CONSTANTS AND STATIC VARIABLES ##############################################
	###############################################################################

	###############################################################################
	# Percentile icons and enums

	# Important constants - declare the percentile icons enum values
	PERC_NO_VALUE = 0;
	PERC_NORMAL = 1;
	PERC_5_PERCENTILE = 2;
	PERC_2_PERCENTILE = 3;
	PERC_1_PERCENTILE = 4;
	PERC_HALF_PERCENTILE = 5;
	PERC_FAILURE = 6;

	enum_perc_list = [ PERC_5_PERCENTILE, PERC_2_PERCENTILE, PERC_1_PERCENTILE, PERC_HALF_PERCENTILE];

	# Display characters for each percentile icon
	PERC_NO_VALUE_CHAR = " ";
	PERC_NORMAL_CHAR = ".";
	PERC_5_PERCENTILE_CHAR = "5";
	PERC_2_PERCENTILE_CHAR = "2";
	PERC_1_PERCENTILE_CHAR = "1";
	PERC_HALF_PERCENTILE_CHAR = "x";
	PERC_FAILURE_CHAR = "?";

	# Display character dictionary:
	perc_disp_char_dict = {
	  PERC_NO_VALUE: PERC_NO_VALUE_CHAR,
	  PERC_NORMAL: PERC_NORMAL_CHAR,
	  PERC_5_PERCENTILE: PERC_5_PERCENTILE_CHAR,
	  PERC_2_PERCENTILE: PERC_2_PERCENTILE_CHAR,
	  PERC_1_PERCENTILE: PERC_1_PERCENTILE_CHAR,
	  PERC_HALF_PERCENTILE: PERC_HALF_PERCENTILE_CHAR,
	  PERC_FAILURE: PERC_FAILURE_CHAR
	};


	# Class variables:
	# Need icon templates for the percentile icons to match against
	# These need to be initialized at runtime
	perc_5_template = None;
	perc_2_template = None;
	perc_1_template = None;
	perc_half_template = None;

	template_perc_list = None;

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
	def __init__(self, perc_enum, image_slice):

		self.perc_enum = perc_enum;

		self.raw_image = image_slice;


	###############################################################################
	# Factory method - given an image slice, returns an enum corresponding to the
	# icon
	@staticmethod
	def get_perc_icon_from_image(slice):

		perc_enum = Hvf_Perc_Icon.get_perc_plot_element(slice);

		return Hvf_Perc_Icon(perc_enum, slice);

	###############################################################################
	# Factory method - given an char, returns an enum corresponding to the
	# icon (used for deserialization)
	@staticmethod
	def get_perc_icon_from_char(icon_char):

		reverse_disp_char_dict = {v: k for k, v in Hvf_Perc_Icon.perc_disp_char_dict.items()}

		try:
			perc_enum = reverse_disp_char_dict[icon_char];
		except:
			perc_enum = Hvf_Perc_Icon.PERC_FAILURE;

		return Hvf_Perc_Icon(perc_enum, None);


	###############################################################################
	# INITIALIZATION METHODS ######################################################
	###############################################################################

	###############################################################################
	# Variable Initialization method - does some preprocessing for variables for
	# ease of calculation
	@classmethod
	def initialize_class_vars(cls):

		# Load the perc icons from a sub-directory -- assumes they are present
		resource_module_dir, _ = os.path.split(pkgutil.get_loader("hvf_extraction_script.hvf_data.perc_icons").get_filename());

		perc_5_template_path = os.path.join(resource_module_dir, "perc_5.JPG");
		perc_2_template_path = os.path.join(resource_module_dir, "perc_2.JPG");
		perc_1_template_path = os.path.join(resource_module_dir, "perc_1.JPG");
		perc_half_template_path = os.path.join(resource_module_dir, "perc_half.JPG");

		cls.perc_5_template = cv2.cvtColor(File_Utils.read_image_from_file(perc_5_template_path), cv2.COLOR_BGR2GRAY);
		cls.perc_2_template = cv2.cvtColor(File_Utils.read_image_from_file(perc_2_template_path), cv2.COLOR_BGR2GRAY);
		cls.perc_1_template = cv2.cvtColor(File_Utils.read_image_from_file(perc_1_template_path), cv2.COLOR_BGR2GRAY);
		cls.perc_half_template = cv2.cvtColor(File_Utils.read_image_from_file(perc_half_template_path), cv2.COLOR_BGR2GRAY);

		#cls.perc_5_template = cv2.cvtColor(File_Utils.read_image_from_file("hvf_extraction_script/hvf_data/perc_icons/perc_5.JPG"), cv2.COLOR_BGR2GRAY);
		#cls.perc_2_template = cv2.cvtColor(File_Utils.read_image_from_file("hvf_extraction_script/hvf_data/perc_icons/perc_2.JPG"), cv2.COLOR_BGR2GRAY);
		#cls.perc_1_template = cv2.cvtColor(File_Utils.read_image_from_file("hvf_extraction_script/hvf_data/perc_icons/perc_1.JPG"), cv2.COLOR_BGR2GRAY);
		#cls.perc_half_template = cv2.cvtColor(File_Utils.read_image_from_file("hvf_extraction_script/hvf_data/perc_icons/perc_half.JPG"), cv2.COLOR_BGR2GRAY);

		# Load them into lists for ease of use:
		cls.template_perc_list = [ cls.perc_5_template, cls.perc_2_template, cls.perc_1_template, cls.perc_half_template ];

		# Lastly, flip the flag to indicate initialization has been done
		cls.is_initialized = True;

		return None;


	###############################################################################
	# OBJECT METHODS ##############################################################
	###############################################################################

	###############################################################################
	# Simple accessor for enum
	def get_enum(self):
		return self.perc_enum;

	###############################################################################
	# Simple accessor for image (NOTE: may be None)
	def get_source_image(self):
		return self.raw_image;

	###############################################################################
	# Simple accessor/toString method
	def get_display_string(self):
		return Hvf_Perc_Icon.perc_disp_char_dict[self.perc_enum];

	###############################################################################
	# Simple equals method
	def is_equal(self, other):
		return (isinstance(other, Hvf_Perc_Icon) and (self.get_enum() == other.get_enum()));

	###############################################################################
	# Releases saved images (to help save memory)
	def release_saved_image(self):

		self.raw_image = None;

		return;


	###############################################################################
	# HELPER METHODS ##############################################################
	###############################################################################


	###############################################################################
	# Helper function for doing template matching:
	@staticmethod
	def do_template_matching(plot_element, w, h, perc_icon):

		# Determine which one is larger
		if (w < np.size(perc_icon, 1)):

			# Plot element is smaller
			scale_factor = min((np.size(perc_icon, 0))/h, (np.size(perc_icon, 1))/w);

			plot_element = cv2.resize(plot_element, (0,0), fx=scale_factor, fy=scale_factor);

		else:
			# perc icon is smaller
			scale_factor = min(h/(np.size(perc_icon, 0)), w/(np.size(perc_icon, 1)));

			perc_icon = cv2.resize(perc_icon, (0,0), fx=scale_factor, fy=scale_factor);

		# Apply template matching:
		temp_matching = cv2.matchTemplate(plot_element, perc_icon, cv2.TM_SQDIFF)

		# Grab our result
		min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(temp_matching);

		return min_val, max_val, min_loc, max_loc;


	###############################################################################
	# Get the corresponding percentile element from the image cell:
	@staticmethod
	def get_perc_plot_element(plot_element):

		# Declare our return value:
		ret_val = Hvf_Perc_Icon.PERC_NO_VALUE;

		# What is the total plot size?
		plot_area = np.size(plot_element, 0) * np.size(plot_element, 1);

		# Delete stray marks; filters out specks based on size compared to global element
		# and relative to largest contour
		plot_threshold = 0.005
		relative_threshold = 0.005
		plot_element = Image_Utils.delete_stray_marks(plot_element, plot_threshold, relative_threshold)

		# First, crop the white border out of the element to get just the core icon:
		x0, x1, y0, y1 = Image_Utils.crop_white_border(plot_element);

		# Calculate height and width:
		h = y1 - y0;
		w = x1 - x0


		# If our bounding indices don't catch any borders (ie, x0 > x1) then its must be an
		# empty element:
		if (w < 0):
			ret_val = Hvf_Perc_Icon.PERC_NO_VALUE


		# Finding 'normal' elements is tricky because the icon is small (scaling doesn't
		# work as easily for it) and it tends to get false matching with other icons
		# However, its size is very different compared to the other icons, so just detect
		# it separately
		# If the cropped bounding box is less than 20% of the overall box, highly likely
		# normal icon
		elif ((h/np.size(plot_element, 0)) < 0.20):

			ret_val = Hvf_Perc_Icon.PERC_NORMAL;

		else:

			# Grab our element icon:
			element_cropped = plot_element[y0:1+y1,x0:1+x1]

			# Now, we template match against all icons and look for best fit:
			best_match = None
			best_perc = None;

			for ii in range(len(Hvf_Perc_Icon.template_perc_list)):

				# Scale up the plot element or perc icon, whichever is smaller
				# (meaning, scale up so they're equal, don't scale down - keep as much
				# data as we can)

				# Grab our perc icon:
				perc_icon = Hvf_Perc_Icon.template_perc_list[ii];

				min_val, max_val, min_loc, max_loc = Hvf_Perc_Icon.do_template_matching(plot_element, w, h, perc_icon);



				# Check to see if this is our best fit yet:
				if (best_match is None or min_val < best_match):
					# This is best fit - record the value and the icon type
					best_match = min_val;
					best_perc = Hvf_Perc_Icon.enum_perc_list[ii];

				# Debug strings for matching the enum:
				debug_string = "Matching enum " + str(Hvf_Perc_Icon.enum_perc_list[ii]) + "; match : " + str(min_val);
				Logger.get_logger().log_msg(Logger.DEBUG_FLAG_DEBUG, debug_string);

			ret_val = best_perc




			# Now we need to ensure that all declared 5-percentile icons are true, because
			# this program often mixes up between 5-percentile and half-percentile

			if (ret_val == Hvf_Perc_Icon.PERC_5_PERCENTILE):


				# Check for contours here - we know that the 5 percentile has multiple small contours
				plot_element = cv2.bitwise_not(plot_element);


				# Find contours. Note we are using RETR_EXTERNAL, meaning no children contours (ie
				# contours within contours)
				contours, hierarchy = cv2.findContours(plot_element,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)

				# Now add up all the contour area
				total_cnt_area = 0;
				for cnt in contours:
					total_cnt_area = total_cnt_area + cv2.contourArea(cnt);


				# Now compare to our cropped area
				# In optimal scenario, 5-percentile takes up 25% of area; half-percentile essentially 100%
				# Delineate on 50%
				AREA_PERCENTAGE_CUTOFF = 0.5;
				area_percentage = total_cnt_area/(w*h);

				Logger.get_logger().log_msg(Logger.DEBUG_FLAG_DEBUG, "Recheck matching betwen 5-percentile and half-percentile");
				Logger.get_logger().log_msg(Logger.DEBUG_FLAG_DEBUG, "Total contour area percentage: " + str(area_percentage));


				# Check to see which is better. Because we are inverting, check max value
				if (area_percentage > AREA_PERCENTAGE_CUTOFF):

					# Half percentile is a better fit - switch our match
					ret_val = Hvf_Perc_Icon.PERC_HALF_PERCENTILE;

					# Declare as such:
					debug_string = "Correction: switching from 5-percentile to half-percentile";
					Logger.get_logger().log_msg(Logger.DEBUG_FLAG_DEBUG, debug_string);


			# Debug strings for bounding box:
			debug_bound_box_string = "Bounding box: " + str(x0) + "," + str(y0) + " ; " + str(x1) + "," + str(y1)
			Logger.get_logger().log_msg(Logger.DEBUG_FLAG_DEBUG, debug_bound_box_string);
			debug_bound_box_dim_string = "Bounding box dimensions: " + str(w) + " , " + str(h);
			Logger.get_logger().log_msg(Logger.DEBUG_FLAG_DEBUG, debug_bound_box_dim_string);

			# And debug function for showing the cropped element:
			show_cropped_element_func = (lambda : cv2.imshow('cropped ' + str(Hvf_Perc_Icon.i), element_cropped))
			Logger.get_logger().log_function(Logger.DEBUG_FLAG_DEBUG, show_cropped_element_func);
			Hvf_Perc_Icon.i = Hvf_Perc_Icon.i+1;

		return ret_val;

	i = 0;
	j = 0;
