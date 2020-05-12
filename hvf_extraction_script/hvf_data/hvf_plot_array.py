###############################################################################
# hvf_plot_array.py
#
# Description:
#	Class definition for an HVF plot array. Essentially is a numpy array
#	representing any plot in the HVF report, which are:
#		Absolute raw plot
#		Absolute deviation (value or percentile)
#		Pattern deviation (value or percentile)
#
# Main usage:
#	Call factory methods to instantiate object (don't use initializer). Two
#	main ways to instantiate a new HVF plot array object:
#		- By passing in image slice of a plot
#		- TODO: Via a serialized text string - uses format from this objects serialization
#
#	To Do:
#
###############################################################################

# Import necessary packages
import cv2
import sys

# Import some helper packages:
import numpy as np
from PIL import Image
from functools import reduce

# Import some of our own written modules:

# For percentile icon detection:
from hvf_extraction_script.hvf_data.hvf_perc_icon import Hvf_Perc_Icon

# For number value detection:
from hvf_extraction_script.hvf_data.hvf_value import Hvf_Value

# For error/debug logging:
from hvf_extraction_script.utilities.logger import Logger

# General purpose image functions:
from hvf_extraction_script.utilities.image_utils import Image_Utils

# General purpose file functions:
from hvf_extraction_script.utilities.file_utils import File_Utils

class Hvf_Plot_Array:


	###############################################################################
	# CONSTANTS AND STATIC VARIABLES ##############################################
	###############################################################################

	###############################################################################
	# Enums to represent type of plot

	PLOT_RAW = "raw";
	PLOT_TOTAL_DEV = "total";
	PLOT_PATTERN_DEV = "pattern";

	PLOT_VALUE = "value";
	PLOT_PERC = "perc";

	###############################################################################
	# Value/string to represent no pattern detect
	NO_PATTERN_DETECT = "Pattern Deviation not shown for severely depressed fields";

	###############################################################################

	NUM_OF_PLOT_ROWS = 10;
	NUM_OF_PLOT_COLS = 10;

	###############################################################################

	BOOLEAN_MASK_24_2 = [
		[0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
		[0, 0, 0, 1, 1, 1, 1, 0, 0, 0],
		[0, 0, 1, 1, 1, 1, 1, 1, 0, 0],
		[0, 1, 1, 1, 1, 1, 1, 1, 1, 0],
		[1, 1, 1, 1, 1, 1, 1, 0, 1, 0],
		[1, 1, 1, 1, 1, 1, 1, 0, 1, 0],
		[0, 1, 1, 1, 1, 1, 1, 1, 1, 0],
		[0, 0, 1, 1, 1, 1, 1, 1, 0, 0],
		[0, 0, 0, 1, 1, 1, 1, 0, 0, 0],
		[0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
	];

	BOOLEAN_MASK_10_2 = [
		[0, 0, 0, 0, 1, 1, 0, 0, 0, 0],
		[0, 0, 1, 1, 1, 1, 1, 1, 0, 0],
		[0, 1, 1, 1, 1, 1, 1, 1, 1, 0],
		[0, 1, 1, 1, 1, 1, 1, 1, 1, 0],
		[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
		[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
		[0, 1, 1, 1, 1, 1, 1, 1, 1, 0],
		[0, 1, 1, 1, 1, 1, 1, 1, 1, 0],
		[0, 1, 1, 1, 1, 1, 1, 1, 0, 0],
		[0, 0, 0, 0, 1, 1, 0, 0, 0, 0]
	];

	BOOLEAN_MASK_30_2 = [
		[0, 0, 0, 1, 1, 1, 1, 0, 0, 0],
		[0, 0, 1, 1, 1, 1, 1, 1, 0, 0],
		[0, 1, 1, 1, 1, 1, 1, 1, 1, 0],
		[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
		[1, 1, 1, 1, 1, 1, 1, 0, 1, 1],
		[1, 1, 1, 1, 1, 1, 1, 0, 1, 1],
		[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
		[0, 1, 1, 1, 1, 1, 1, 1, 1, 0],
		[0, 0, 1, 1, 1, 1, 1, 1, 0, 0],
		[0, 0, 0, 1, 1, 1, 1, 0, 0, 0]
	];


	# 2D array specifying what elements should/should not be evaluated (ie, known
	# empty cells for ALL plot sizes). It essentially follows 30-2 (without blind
	# spot)
	PLOT_ELEMENT_BOOLEAN_MASK = [
		[0, 0, 0, 1, 1, 1, 1, 0, 0, 0],
		[0, 0, 1, 1, 1, 1, 1, 1, 0, 0],
		[0, 1, 1, 1, 1, 1, 1, 1, 1, 0],
		[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
		[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
		[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
		[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
		[0, 1, 1, 1, 1, 1, 1, 1, 1, 0],
		[0, 0, 1, 1, 1, 1, 1, 1, 0, 0],
		[0, 0, 0, 1, 1, 1, 1, 0, 0, 0]
	];


	###############################################################################

	# Define triangle icon variable to hold the template to match against:
	triangle_icon_template = None;

	###############################################################################
	# CONSTRUCTOR AND FACTORY METHODS #############################################
	###############################################################################


	###############################################################################
	# Initializer method
	# Not to be used publicly - use factory methods instead
	# Takes in pertinent data
	def __init__(self, plot_type, icon_type, plot_array, plot_image):

		self.plot_type = plot_type;
		self.icon_type = icon_type;

		self.plot_array = plot_array

		self.plot_image = plot_image;


	###############################################################################
	# Factory method - get a plot from image
	@staticmethod
	def get_plot_from_image(hvf_image_gray, plot_type, icon_type, y_ratio, y_size, x_ratio, x_size):

		plot_array = None;
		plot_img = None;

		# If this is a pattern plot, make sure to check if pattern was generated:
		if (plot_type == Hvf_Plot_Array.PLOT_PATTERN_DEV and Hvf_Plot_Array.is_pattern_not_shown(hvf_image_gray, y_ratio, y_size, x_ratio, x_size)):

			plot_array = Hvf_Plot_Array.NO_PATTERN_DETECT;

		else:

			plot_array, plot_img = Hvf_Plot_Array.get_plot(hvf_image_gray, y_ratio, y_size, x_ratio, x_size, plot_type, icon_type);

		return Hvf_Plot_Array(plot_type, icon_type, plot_array, plot_img);


	###############################################################################
	# Factory method - get a plot from array (for use in deserialization)
	@staticmethod
	def get_plot_from_array(plot_type, icon_type, plot_array):
		return Hvf_Plot_Array(plot_type, icon_type, plot_array, None);


	###############################################################################
	# Variable Initialization method
	@classmethod
	def initialize_class_vars(cls):

		# Load the icons from a sub-directory -- assumes they are present
		cls.triangle_icon_template = cv2.cvtColor(File_Utils.read_image_from_file("hvf_extraction_script/hvf_data/other_icons/icon_triangle.PNG"), cv2.COLOR_BGR2GRAY);

		# Lastly, flip the flag to indicate initialization has been done
		cls.is_initialized = True;

		return None;



	###############################################################################
	# OBJECT METHODS ##############################################################
	###############################################################################

	###############################################################################
	# Simple accessor for plot type
	def get_plot_type(self):
		return self.plot_type;

	###############################################################################
	# Simple accessor for icon type
	def get_icon_type(self):
		return self.icon_type;

	###############################################################################
	# Simple accessor for plot array
	def get_plot_array(self):
		return self.plot_array;

	###############################################################################
	# Simple accessor for plot array
	def get_source_image(self):
		return self.plot_image;


	###############################################################################
	# Get display string for array:
	def get_display_string(self, delimiter):

		# Check if pattern plot/no pattern generated
		if (self.is_pattern_not_generated()):
			return self.plot_array
		else:
			return Hvf_Plot_Array.get_array_string(self.plot_array, self.icon_type, delimiter);

	###############################################################################
	# Get list of display string for each row in array (for serialization
	def get_display_string_list(self, delimiter):

		# Check if pattern plot/no pattern generated
		if (self.is_pattern_not_generated()):
			return self.plot_array
		else:

			return_list = [];
			for r in range(0, np.size(self.plot_array, 1)):
				return_list.append(Hvf_Plot_Array.get_array_string_by_line(self.plot_array, self.icon_type, delimiter, r));

			return return_list;

	###############################################################################
	# Returns boolean if this is a pattern plot that has no pattern detected
	# Useful for checking prior to access plot_array for other functions
	def is_pattern_not_generated(self):
		return (isinstance(self.plot_array, str) and (self.plot_array == Hvf_Plot_Array.NO_PATTERN_DETECT));



	###############################################################################
	# Releases saved images (to help save memory)
	def release_saved_image(self):

		self.plot_image = None;

		# Check if pattern plot/no pattern generated
		if not self.is_pattern_not_generated():

			for r in range(0, np.size(self.plot_array, 0)):
				for c in range (0, np.size(self.plot_array, 1)):

					self.plot_array[r][c].release_saved_image();

		return;

	###############################################################################
	# HELPER METHODS ##############################################################
	###############################################################################


	###############################################################################
	# PATTERN DEVIATION DETECTION METHODS #########################################
	###############################################################################
	# Pattern deviation is not always shown (if field is too severely depressed).
	# Need to specially detect this case to elegantly handle it.

	###############################################################################
	# Searches for specific text stating that pattern is not performed. If the text
	# matches with high enough score, returns true
	def is_pattern_not_shown(hvf_image_gray, y_ratio, y_size, x_ratio, x_size):

		# Calculate height/width for calculation later:
		height = np.size(hvf_image_gray, 0)
		width = np.size(hvf_image_gray, 1)


		# Slice image:
		hvf_image_gray = Image_Utils.preprocess_image(hvf_image_gray);
		sliced_img = Image_Utils.slice_image(hvf_image_gray, y_ratio, y_size, x_ratio, x_size)

		# Try to detect a bounding box:
		top_left, w, h = Hvf_Plot_Array.get_bounding_box(sliced_img);

		# Calculate the relative (percentage) size of the bounding box compared to slice:
		box_ratio_w = w/(x_size*width);
		box_ratio_h = h/(y_size*height);

		# Define a threshold below which if the size ratio is, we declare that the pattern
		# is not detected:
		threshold_size = 0.3;


		return (box_ratio_w < threshold_size or box_ratio_h < threshold_size);





	###############################################################################
	# IMAGE PROCESSING METHODS ####################################################
	###############################################################################

	###############################################################################
	# Get the plot within the image passed in, bounded by slice parameters
	# Plot_type is either "perc" or "value" - this will determine how to match/identify
	# each cell (used in a downstream function)
	@staticmethod
	def get_plot(hvf_image_gray, y_ratio, y_size, x_ratio, x_size, plot_type, icon_type):

		plot_image = Image_Utils.slice_image(hvf_image_gray, y_ratio, y_size, x_ratio, x_size)

		hvf_image_gray_process = Image_Utils.preprocess_image(hvf_image_gray.copy());
		plot_image_process = Image_Utils.slice_image(hvf_image_gray_process, y_ratio, y_size, x_ratio, x_size)

		# Get bounding box from processed image:
		top_left, w, h = Hvf_Plot_Array.get_bounding_box(plot_image_process);
		bottom_right = (top_left[0] + w, top_left[1] + h);


		# Need to specifically handle raw value plot - can have a discontinuity in the
		# x axis (with triangle icon), which causes a mis-fit. So need to fill in x-axis
		# and try again

		cv2.line(plot_image_process, (top_left[0], top_left[1]+int(h/2)), (top_left[0]+w, top_left[1]+int(h/2)), (0), max(int(h*0.015), 1));

		top_left, w, h = Hvf_Plot_Array.get_bounding_box(plot_image_process);
		bottom_right = (top_left[0] + w, top_left[1] + h);

		# For debugging: Draw rectangle around the plot - MUST BE COMMENTED OUT, BECAUSE
		# IT WILL INTERFERE WITH LATER PLOT EXTRACTIONS
		#cv2.rectangle(plot_image, top_left, bottom_right, 0, 2)

		# Debug function for showing the plot:
		#show_plot_func = (lambda : cv2.imshow("Bound rect for plot " + plot_type, plot_image))
		#Logger.get_logger().log_function(Logger.DEBUG_FLAG_DEBUG, show_plot_func);
		#cv2.waitKey();

		# Slice out the axes plot on the original:
		tight_plot = plot_image[top_left[1]:(top_left[1] + h), top_left[0]:(top_left[0] + w)];

		# And extract the values from the array:
		plot_array = Hvf_Plot_Array.extract_values_from_plot(tight_plot, plot_type, icon_type)

		# Return the array:
		return plot_array, tight_plot;

	###############################################################################
	# Generates a template for matching to the pattern deviation plot
	def generate_plot_template(w, h):

		# Create a white grayscale image
		template = np.ones((h,w,1), np.uint8)*255;

		# Draw the black axes in the middle. We want to leave some whites at the end of the
		# lines on either ends to match against the endpoints of the axes plot
		white_border_size = 0.0;

		cv2.line(template, (int(w/2), int(h*white_border_size)), (int(w/2), int(h*(1-white_border_size))), (0), 3);
		cv2.line(template, (int(w*white_border_size), int(h/2)), (int(w*(1-white_border_size)), int(h/2)), (0), 3);


		return template;


	###############################################################################
	# Generates a mask for matching the template to the pattern deviation plot
	def generate_plot_mask(w, h):

		# Create a baseline mask image
		# 0s are transparent
		mask = np.zeros((h, w,1), np.uint8);


		# Draw axes in the middle (to allow mask to match template on)
		cv2.line(mask, (int(w/2), 0), (int(w/2), h), (255), 1);
		cv2.line(mask, (0, int(h/2)), (w, int(h/2)), (255), 1);

		return mask;


	###############################################################################
	# Generates a mask for matching the template to the pattern deviation plot
	def generate_corner_mask(w, h):

		# Create a baseline mask image
		# 0s are transparent
		mask = np.ones((h,w,1), np.uint8)*255;

		# Defines size of each side (by ratio to full mask)
		ratio = 0.2


		# Top left corner:
		# Note thickness is -1 --> indicates area should be filled in
		cv2.rectangle(mask,(0,0),(int(w*ratio),int(h*ratio)),(0), -1)

		# Top right corner:
		cv2.rectangle(mask,(int(w*(1-ratio)),0),(w,int(h*ratio)),(0), -1)

		# Bottom left corner:
		cv2.rectangle(mask,(0,int(h*(1-ratio))),(int(w*ratio),h),(0), -1)

		# Bottom right corner:
		cv2.rectangle(mask,(int(w*(1-ratio)),int(h*(1-ratio))),(w,h),(0), -1)

		return mask;

	###############################################################################
	# Generates bounding box for the pattern deviation plot. Assumes that sliced_image is
	# centered on axes of interest and no other large axes exist (searches based on size)

	# First, define a helper function for sorting:
	def contour_sort_max_dim(cntr):
		x,y,w,h = cv2.boundingRect(cntr);

		return max(w, h);

	def contour_bound_box_area(c):
		x,y,w,h = cv2.boundingRect(c);
		return w*h;

	def get_bounding_box(sliced_image):

		# To get the best bounding box, first we preprocess frame, then search for the largest
		# width/length based on contours, and recenter over the cross with those best
		# dimensions

		# Copy argument plot, and invert black/white (as we're looking for contours)
		tighter_slice = cv2.bitwise_not(sliced_image.copy());
		w = np.size(tighter_slice, 1);
		h = np.size(tighter_slice, 0);

		# Preprocess this image - we need to bold out axes to eliminate any breaks from noise
		# Perform dilation
		kernel = np.ones((3,3),np.uint8);
		tighter_slice = cv2.dilate(tighter_slice, None,iterations = 1)

		# Before doing contours, draw a black border 1px wide (bc contours don't detect objects
		# that touch the border
		cv2.rectangle(tighter_slice, (0,0), (w,h), 0, 1)

		# Now, find contours, sort by max dimension
		contours, _ = cv2.findContours(tighter_slice,cv2.RETR_LIST,cv2.CHAIN_APPROX_SIMPLE)
		contours = sorted(contours, key = Hvf_Plot_Array.contour_bound_box_area, reverse = True)[:5]

		# Grab the width/height of the largest contour:
		best_width = cv2.boundingRect(contours[0])[2];
		best_height = cv2.boundingRect(contours[0])[3];

		# Do another template match to get best fit:
		best_template = Hvf_Plot_Array.generate_plot_template(best_width, best_height);
		best_mask = Hvf_Plot_Array.generate_plot_mask(best_width, best_height);
		best_data = np.zeros((best_height, best_width, 1), np.uint8);
		bounding_box = cv2.matchTemplate(sliced_image, best_template, cv2.TM_SQDIFF, best_data, best_mask);

		# Grab our result
		min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(bounding_box);

		# Return the bounding box. This box is centered on the axes
		return min_loc, best_width, best_height;


	###############################################################################
	# Given a plot, looks for the triangle icon and deletes it, if found with
	# high enough certainty
	# Only to be called with raw plots
	@staticmethod
	def find_and_delete_triangle_icon(plot_image):
		TRIANGLE_TO_PLOT_RATIO_W = 0.0305

		THRESHOLD_MATCH = 0.6;

		# First, copy and resize the template icon:
		triangle_icon = Hvf_Plot_Array.triangle_icon_template.copy();

		scale_factor = (np.size(plot_image, 1)*TRIANGLE_TO_PLOT_RATIO_W)/np.size(triangle_icon, 1);

		triangle_icon = cv2.resize(triangle_icon, (0,0), fx=scale_factor, fy=scale_factor)

		# Template match to find icon:
		temp_matching = cv2.matchTemplate(plot_image, triangle_icon, cv2.TM_CCOEFF_NORMED)

		# Grab our result
		min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(temp_matching);

		# If we have a match, white out the triangle area
		if (max_val > THRESHOLD_MATCH):
			Logger.get_logger().log_msg(Logger.DEBUG_FLAG_INFO, "Found triangle icon, deleting it");

			# Get our corners:
			top_left = max_loc
			bottom_right = (max_loc[0] + np.size(triangle_icon, 1), max_loc[1] + np.size(triangle_icon, 0));

			# Declare some pertinent values for the bottom edge of the matching:
			x_start = top_left[0];
			x_end = bottom_right[0];
			row_index = bottom_right[1]

			# We will lengthen the bottom edge until some percentage of pixel start appearing whites
			# Need to calculate this threshold:
			num_pix = x_end - x_start;
			PERCENTAGE_THRESHOLD = .10
			WHITE_PIXEL_VALUE = 255
			threshold_pixel_value = int(PERCENTAGE_THRESHOLD*num_pix*WHITE_PIXEL_VALUE)

			Logger.get_logger().log_msg(Logger.DEBUG_FLAG_DEBUG, "Number of pixel at border: ({}, {}) => {}".format(str(x_start), str(x_end), str(num_pix)));
			Logger.get_logger().log_msg(Logger.DEBUG_FLAG_DEBUG, "Threshold pixel value: " + str(threshold_pixel_value));
			# The bottom line tends to be problematic (still some residual Left
			# after erasing matching icon) so manually look for residual
			while True:
				sum_pixels = sum(plot_image[row_index, x_start:x_end])
				Logger.get_logger().log_msg(Logger.DEBUG_FLAG_DEBUG, "Sum pixels: " + str(sum_pixels));

				if (sum_pixels < threshold_pixel_value):
					Logger.get_logger().log_msg(Logger.DEBUG_FLAG_INFO, "Lengthening triangle box to cover residual");
					row_index = row_index+1
				else:
					break;

			cv2.rectangle(plot_image,top_left,(x_end, row_index),(255), -1)
			#cv2.rectangle(plot_image,max_loc,(x_end, row_index),(0), 1)
		else:
			Logger.get_logger().log_msg(Logger.DEBUG_FLAG_INFO, "Did not find triangle icon, matching value " + str(max_val));

	###############################################################################
	# Given a plot image (axes deleted), returns an array of dimension fractions
	# corresponding to column/row grid lines to split apart plot elements
	# Always returns list of 11 elements

	def contour_x_dim(c):
		x,y,w,h = cv2.boundingRect(c);
		return x;

	def contour_y_dim(c):
		x,y,w,h = cv2.boundingRect(c);
		return y;

	def get_contour_centroid(c):
		M = cv2.moments(array = c)

		if (M['m00'] == 0):
			cx = 0;
			cy = 0;
		else:
			cx = int(M['m10'] / M['m00'])
			cy = int(M['m01'] / M['m00'])

		return (cx, cy);

	def get_plot_grid_lines(plot_image, plot_type, icon_type):

		Logger.get_logger().log_msg(Logger.DEBUG_FLAG_INFO, "Finding grid lines");

		plot_w = np.size(plot_image, 1)
		plot_h = np.size(plot_image, 0)

		horizontal_img = plot_image.copy();
		vertical_img = plot_image.copy();

	    # [Horizontal]
	    # Specify size on horizontal axis
		horizontal_size = horizontal_img.shape[1]

	    # Create structure element for extracting horizontal lines through morphology operations
		horizontalStructure = cv2.getStructuringElement(cv2.MORPH_RECT, (horizontal_size, 1))

		# Apply morphology operations
		horizontal_img = cv2.morphologyEx(horizontal_img, cv2.MORPH_OPEN, horizontalStructure, iterations = 2)
		#horizontal_img = cv2.erode(horizontal_img, horizontalStructure)
		#horizontal_img = cv2.dilate(horizontal_img, horizontalStructure)

		# Then, take a slice from the middle of the plot, and find contours
		# We will use this to help find grid lines
		horizontal_slice = Image_Utils.slice_image(horizontal_img, 0, 1, 0.475, 0.05)
		horizontal_slice = cv2.copyMakeBorder(horizontal_slice,0,0,1,1,cv2.BORDER_CONSTANT, 0);

		# Then, find contours (of the blank spaces) and convert to their respective centroid:
		horizontal_cnts, hierarchy = cv2.findContours(horizontal_slice, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

		centroid_horizontal = list(map((lambda c: Hvf_Plot_Array.get_contour_centroid(c)[1]/plot_h), horizontal_cnts));

	    # [Vertical]
	    # Specify size on vertical axis
		vertical_size = vertical_img.shape[1];

	    # Create structure element for extracting vertical lines through morphology operations
		verticalStructure = cv2.getStructuringElement(cv2.MORPH_RECT, (1, vertical_size))

		# Apply morphology operations
		vertical_img = cv2.morphologyEx(vertical_img, cv2.MORPH_OPEN, verticalStructure, iterations = 2)
		#vertical_img = cv2.erode(vertical_img, verticalStructure)
		#vertical_img = cv2.dilate(vertical_img, verticalStructure)

		# Then, take a slice from the middle of the plot, and find contours
		# We will use this to help find grid lines
		vertical_slice = Image_Utils.slice_image(vertical_img, 0.475, 0.05, 0, 1)
		vertical_slice = cv2.copyMakeBorder(vertical_slice,1,1,0,0,cv2.BORDER_CONSTANT, 0);

		# Then, find contours (of the blank spaces) and convert to their respective centroid:
		vertical_cnts, hierarchy = cv2.findContours(vertical_slice, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

		centroid_vertical = list(map((lambda c: Hvf_Plot_Array.get_contour_centroid(c)[0]/plot_w), vertical_cnts));

		# Now, we need to find the grid lines
		# We assume grid lines are centered in the middle of plot image (since they
		# are detected that way). Have prelim grid lines, and move then accordingly
		# to fit into empty spaces


		# Columns:
		col_list = [];

		# Pre-calculate some values:
		slice_w = np.size(vertical_slice, 1)
		slice_h = np.size(vertical_slice, 0)

		for c in range(Hvf_Plot_Array.NUM_OF_PLOT_COLS+1):

			# Get our prelim column value:
			col_val = 0.5-(0.097*(5-c))

			# Precalculate our coordinates to check:
			y = int(slice_h*0.5);
			x = int(col_val*slice_w);

			if (x >= slice_w):
				x = slice_w-1;

			# If this grid line does not coincide with a plot element area, then its good

			if (vertical_slice[y,x] == 255):
				# Grid line falls into blank area - we can record value
				Logger.get_logger().log_msg(Logger.DEBUG_FLAG_INFO, "Prelim column {} grid line works".format(c));
				col_list.append(col_val);

			else:
				# It coincides -> convert it to the closest centroid of a blank area
				Logger.get_logger().log_msg(Logger.DEBUG_FLAG_INFO, "Shifting column grid line {} to nearest centroid".format(c));
				closest_centroid = list(sorted(centroid_vertical, key = (lambda x: abs(x-col_val))))[0];

				col_list.append(closest_centroid);

		# Rows:
		row_list = [];

		# Pre-calculate some values:
		slice_w = np.size(horizontal_slice, 1)
		slice_h = np.size(horizontal_slice, 0)
		for r in range(Hvf_Plot_Array.NUM_OF_PLOT_ROWS+1):

			# Get our prelim row value:
			row_val = 0.5-(0.095*(5-r))

			# Precalculate our coordinates to check:
			y = int(row_val*slice_h);
			x = int(slice_w*0.5);

			if (y >= slice_h):
				y = slice_h-1;

			# If this grid line does not coincide with a plot element area, then its good


			if (horizontal_slice[y,x] == 255):
				# Grid line falls into blank area - we can record value
				Logger.get_logger().log_msg(Logger.DEBUG_FLAG_INFO, "Prelim row {} grid line works".format(r));
				row_list.append(row_val);

			else:
				# It coincides -> convert it to the closest centroid of a blank area
				Logger.get_logger().log_msg(Logger.DEBUG_FLAG_INFO, "Shifting row grid line {} to nearest centroid".format(r));
				closest_centroid = list(sorted(centroid_horizontal, key = (lambda y: abs(y-row_val))))[0];

				row_list.append(closest_centroid);


		# Collect our two lists and return them together:
		return_dict = {};
		return_dict['row_list'] = row_list;
		return_dict['col_list'] = col_list;


		return return_dict;

	###############################################################################
	# Extract all elements from a plot. Returns values as 10x10 array
	# Plot type is either "perc" or "value"
	# The overall plot distribution:
	# Eg, OD 24-2:
	#       x x | x x
	#     x x x | x x x
	#   x x x x | x x x x
	# x x x x x | x x   x
	# -------------------
	# x x x x x | x x   x
	#   x x x x | x x x x
	#     x x x | x x x
	#       x x | x x

	# Eg, OD 30-2:
	#       x x | x x
	#     x x x | x x x
	#   x x x x | x x x x
	# x x x x x | x x x x x
	# x x x x x | x x   x x
	# ---------------------
	# x x x x x | x x   x x
	# x x x x x | x x x x x
	#   x x x x | x x x x
	#     x x x | x x x
	#       x x | x x
	def extract_values_from_plot(plot_image, plot_type, icon_type):

		# First, image process for best readability:
		#plot_image = cv2.GaussianBlur(plot_image, (5,5), 0)

		plot_image_backup = plot_image.copy();

		# Perform image processing depending on plot type:
		if (icon_type == Hvf_Plot_Array.PLOT_PERC):
			plot_image = cv2.bitwise_not(cv2.adaptiveThreshold(plot_image,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY_INV,11,5));
		elif (icon_type == Hvf_Plot_Array.PLOT_VALUE):
			#plot_image = cv2.GaussianBlur(plot_image, (5,5), 0)
			ret2, plot_image = cv2.threshold(plot_image,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)

			kernel_size = 31;
			mean_offset = 15;
			plot_image_backup = cv2.bitwise_not(cv2.adaptiveThreshold(plot_image_backup,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY_INV,kernel_size,mean_offset));

			kernel = np.ones((3,3),np.uint8)


		# For readability, grab our height/width:
		plot_width = np.size(plot_image, 1)
		plot_height = np.size(plot_image, 0)

		# The elements are laid out roughly within a 10x10 grid
		NUM_CELLS_ROW = Hvf_Plot_Array.NUM_OF_PLOT_ROWS
		NUM_CELLS_COL = Hvf_Plot_Array.NUM_OF_PLOT_COLS

		# Delete triangle icon, if we can find it:
		if (plot_type == Hvf_Plot_Array.PLOT_RAW):
			Hvf_Plot_Array.find_and_delete_triangle_icon(plot_image);

		# Mask out corners:
		corner_mask = Hvf_Plot_Array.generate_corner_mask(plot_width, plot_height);
		plot_image = cv2.bitwise_or(plot_image, cv2.bitwise_not(corner_mask));

		# First, declare our return value array, no need to really initialize bc we'll
		# iterate through it
		plot_values_array = 0;

		if (icon_type == Hvf_Plot_Array.PLOT_PERC):
			plot_values_array = np.zeros((NUM_CELLS_COL, NUM_CELLS_ROW), dtype=Hvf_Perc_Icon);

		elif (icon_type == Hvf_Plot_Array.PLOT_VALUE):
			plot_values_array = np.zeros((NUM_CELLS_COL, NUM_CELLS_ROW), dtype=Hvf_Value);

		# We can also eliminate the grid axes/lines because we don't need them anymore, and
		# they will make the image detection harder
		# Just draw white lines along the axes
		# Depending on type of plot, we need a thicker line to cover up the axes
		# (raw needs thicker because they have axis markers, everything else needs thinner)
		axes_size = 0;
		if (plot_type == Hvf_Plot_Array.PLOT_RAW):
			axes_size = 0.03
		else:
			axes_size = 0.0135

		cv2.line(plot_image, (int(plot_width/2), 0), (int(plot_width/2), plot_height), (255), max(int(plot_width*axes_size), 1));
		cv2.line(plot_image, (0, int(plot_height/2)), (plot_width, int(plot_height/2)), (255), max(int(plot_height*axes_size), 1));

		# Grab the grid lines:
		grid_line_dict = Hvf_Plot_Array.get_plot_grid_lines(plot_image, plot_type, icon_type);


		plot_image_debug_copy = plot_image.copy();
		# Debug code - draws out slicing for the elements on the plot:
		for c in range(Hvf_Plot_Array.NUM_OF_PLOT_COLS+1):
			x = int(grid_line_dict['col_list'][c]*plot_width)
			cv2.line(plot_image_debug_copy, (x, 0), (x, plot_height), (0), 1);

		for r in range (Hvf_Plot_Array.NUM_OF_PLOT_ROWS+1):
			y = int(grid_line_dict['row_list'][r]*plot_height)
			cv2.line(plot_image_debug_copy, (0, y), (plot_width, y), (0), 1);

		# Debug function for showing the plot:
		show_plot_func = (lambda : cv2.imshow("plot " + icon_type, plot_image_debug_copy))
		Logger.get_logger().log_function(Logger.DEBUG_FLAG_DEBUG, show_plot_func);

		# We iterate through our array, then slice out the appropriate cell from the plot
		for x in range(0, NUM_CELLS_COL):
			for y in range(0, NUM_CELLS_ROW):

				# Debug info for indicating what cell we're computing:
				Logger.get_logger().log_msg(Logger.DEBUG_FLAG_INFO, "Cell " + str(x) + "," + str(y));

				# Grab our cell slice for the plot element
				# (remember arguments: slice_image(image, y_ratio, y_size, x_ratio, x_size):

				# The height of the axes tends to extend ~2.5% past the elements on top, bottom
				# The width of the axes tends to extend
				# So we take that into account when we take the slice

				row_grid_val = grid_line_dict['row_list'][y]
				row_grid_val_size = grid_line_dict['row_list'][y+1] - grid_line_dict['row_list'][y];

				col_grid_val = grid_line_dict['col_list'][x]
				col_grid_val_size = grid_line_dict['col_list'][x+1] - grid_line_dict['col_list'][x];

				cell_slice = Image_Utils.slice_image(plot_image, row_grid_val, row_grid_val_size, col_grid_val, col_grid_val_size);
				cell_slice_backup = Image_Utils.slice_image(plot_image_backup, row_grid_val, row_grid_val_size, col_grid_val, col_grid_val_size);

				cell_object = 0;

				# Then, need to analyze to figure out what element is in this position
				# What we look for depends on type of plot - perc vs value
				if (icon_type == Hvf_Plot_Array.PLOT_PERC):

					if (Hvf_Plot_Array.PLOT_ELEMENT_BOOLEAN_MASK[y][x]):
						# This element needs to be detected

						# Because this step relies on many things going right, possible that our
						# slices are not amenable to template matching and cause an error
						# So, try it under a try-except clause. If failure, we place a failure
						# placeholder

						try:
							cell_object = Hvf_Perc_Icon.get_perc_icon_from_image(cell_slice)
							Logger.get_logger().log_msg(Logger.DEBUG_FLAG_INFO, "Percentile Icon detected: " + cell_object.get_display_string());

						except:
							Logger.get_logger().log_msg(Logger.DEBUG_FLAG_WARNING, "Cell " + str(x) + "," + str(y) + ": Percentile icon detection failure");
							cell_object = Hvf_Perc_Icon.get_perc_icon_from_char(Hvf_Perc_Icon.PERC_FAILURE_CHAR);
							raise Exception(str(e))

					else:
						# This is a no-detect element, so just instantiate a blank:
						cell_object = Hvf_Perc_Icon.get_perc_icon_from_char(Hvf_Perc_Icon.PERC_NO_VALUE_CHAR);
						Logger.get_logger().log_msg(Logger.DEBUG_FLAG_INFO, "Masking element - generating NO VALUE element");



				elif (icon_type == Hvf_Plot_Array.PLOT_VALUE):


					if (Hvf_Plot_Array.PLOT_ELEMENT_BOOLEAN_MASK[y][x]):
						# This element needs to be detected

						# Because this step relies on many things going right, possible that our
						# slices are not amenable to template matching and cause an error
						# So, try it under a try-except clause. If failure, we place a failure
						# placeholder to fix later

						try:
							cell_object = Hvf_Value.get_value_from_image(cell_slice, cell_slice_backup, plot_type);
							Logger.get_logger().log_msg(Logger.DEBUG_FLAG_INFO, "Value detected: " + cell_object.get_display_string());


						except Exception as e:
							Logger.get_logger().log_msg(Logger.DEBUG_FLAG_WARNING, "Cell " + str(x) + "," + str(y) + ": Value detection failure");
							cell_object = Hvf_Value.get_value_from_display_string(Hvf_Value.VALUE_FAILURE);
							raise Exception(str(e))

					else:
						# This is a no-detect element, so just instantiate a blank:
						cell_object = Hvf_Value.get_value_from_display_string(Hvf_Value.VALUE_NO_VALUE);
						Logger.get_logger().log_msg(Logger.DEBUG_FLAG_INFO, "Masking element - generating NO VALUE element");


				Logger.get_logger().log_msg(Logger.DEBUG_FLAG_INFO, "=====");


				# Lastly, store into array:
				plot_values_array[x, y] = cell_object;


		wait_func = (lambda : cv2.waitKey(0));
		Logger.get_logger().log_function(Logger.DEBUG_FLAG_DEBUG, wait_func);
		destroy_windows_func = (lambda : cv2.destroyAllWindows() );
		Logger.get_logger().log_function(Logger.DEBUG_FLAG_DEBUG, destroy_windows_func);


		# Return our array:
		return plot_values_array;

	###############################################################################
	# STRING METHODS ##############################################################
	###############################################################################


	###############################################################################
	# Converts array into readable string
	# Uses the delimiter passed in as an argument
	# Assumes plot_array is array of cell objects (hvf_value or hvf_perc_icon)
	def get_array_string(plot_array, icon_type, delimiter):

		ret_string = "";

		# Have to iterate in an odd way because of the way the array is organized
		for i in range(0, np.size(plot_array, 1)):

			ret_string = ret_string + Hvf_Plot_Array.get_array_string_by_line(plot_array, icon_type, delimiter, i) + "\n\n";

		return ret_string


	###############################################################################
	# Converts the specified array row into string
	# Uses the delimiter passed in as an argument
	# Assumes array_arg is a numpy array
	# First index is x-axis (column), second index is y-axis (row)
	# Because we want human-readable string, we index to pull out an entire row (ie, fixed y)
	def get_array_string_by_line(plot_array, icon_type, delimiter, y_index):

		row_array = plot_array[:,y_index]
		string_array = "";

		if (icon_type == Hvf_Plot_Array.PLOT_VALUE):
			row_array = map((lambda x: x.get_standard_size_display_string()), row_array)

		elif (icon_type == Hvf_Plot_Array.PLOT_PERC):
			row_array = map((lambda x: x.get_display_string()), row_array)

		ret_string = delimiter.join(row_array)

		return ret_string
