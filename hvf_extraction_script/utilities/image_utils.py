###############################################################################
# image_utils.py
#
# Description:
#	Class definition for commonly used, general use image functions
#
###############################################################################

# Import necessary packages
import cv2
import sys

# Import some helper packages:
import numpy as np
from PIL import Image
from functools import reduce

# For error/debug logging:
from hvf_extraction_script.utilities.logger import Logger

class Image_Utils:


	###############################################################################
	# CONSTANTS AND STATIC VARIABLES ##############################################
	###############################################################################

	###############################################################################
	# IMAGE PROCESSING METHODS ####################################################
	###############################################################################

	###############################################################################
	# Preprocessing image to enhance image quality
	@staticmethod
	def preprocess_image(image):

		# Look up how to optimize/preprocess images for tesseract - this is a common issue

		# Median Blurring:
		#image = cv2.medianBlur(image, 7)

		# Gaussian Blurring:
		#image = cv2.GaussianBlur(image,(3,3),0)

		# Thresholding:
		#image = cv2.threshold(image, 127, 255, cv2.THRESH_BINARY)[1];

		# This works out to best best preprocess - esp for photo images that have variable
		# lighting
		image = cv2.adaptiveThreshold(image,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY,11,2)

		return image;


	###############################################################################
	# Given starting coordinates and corresponding slice sizes (all in fractions of
	# the total image size), slices the input image. This uses Numpy slicing
	@staticmethod
	def slice_image(image, y_ratio, y_size, x_ratio, x_size):

		# Calculate height/width for slicing later:
		height = np.size(image, 0)
		width = np.size(image, 1)

		# Calculate the starting and ending indices of y and x:
		y1 = int(height*y_ratio);
		y2 = int(height*(y_ratio+y_size));

		x1 = int(width*x_ratio);
		x2 = int(width*(x_ratio+x_size));

		image_slice = image[y1:y2, x1:x2];

		return image_slice;


	###############################################################################
	# Given an image, returns the coordinates cropping the image (ie, eliminates white
	# border). Returns bounding x's and y's
	@staticmethod
	def crop_white_border(image):


		# Crop out the borders so we just have the central values - this allows us
		# to standardize size
		# First, crop the white border out of the element to get just the core icon:
		x0, y0 = 0,0;
		x1, y1 = np.size(image, 1)-1,np.size(image, 0)-1;

		element_mask = image > 0

		# Find bounding ys:
		for row_index in range(0, np.size(image, 0)):
			if reduce((lambda x,y: x and y), element_mask[row_index,:]) == True: # All white row
				y0 = row_index;
				continue;
			else: # We have at least 1 black pixel - stop
				break;


		for row_index in range(np.size(image, 0)-1, 0, -1):
			if reduce((lambda x,y: x and y), element_mask[row_index,:]) == True: # All white row
				y1 = row_index;
				continue;
			else: # We have at least 1 black pixel - stop
				break;


		# Find bounding xs:
		for col_index in range(0, np.size(image, 1)):
			if reduce((lambda x,y: x and y), element_mask[:,col_index]) == True: # All white row
				x0 = col_index;
				continue;
			else: # We have at least 1 black pixel - stop
				break;


		for col_index in range(np.size(image, 1)-1, 0, -1):
			if reduce((lambda x,y: x and y), element_mask[:,col_index]) == True: # All white row
				x1 = col_index;
				continue;
			else: # We have at least 1 black pixel - stop
				break;


		return x0, x1, y0, y1;

	###############################################################################
	# Helper function for bounding box area of a contour
	def contour_bound_box_area(x):
	  x,y,w,h = cv2.boundingRect(x);
	  return w*h;

	###############################################################################
	# Given a image, masks out contours of a certain size or smaller (based
	# on fraction of total plot element or relative to largest contour)
	@staticmethod
	def delete_stray_marks(image, global_threshold, relative_threshold):

	  # Threshold by area when to remove a contour:
	  plot_area = np.size(image, 0) * np.size(image, 1);

	  image_temp = cv2.bitwise_not(image.copy());
	  cnts, hierarchy = cv2.findContours(image_temp, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
	  mask = np.ones(image_temp.shape[:2], dtype="uint8") * 255


	  # We want to eliminate small contours. Define relative to entire plot area and/or
	  # relative to largest contour
	  cnts = sorted(cnts, key = Image_Utils.contour_bound_box_area, reverse = True);

	  largest_contour_area = 0;

	  if (len(cnts) > 0):
	    largest_contour_area = Image_Utils.contour_bound_box_area(cnts[0]);


	  contours_to_mask = [];

	  # Loop over the contours
	  Logger.get_logger().log_msg(Logger.DEBUG_FLAG_DEBUG, "Looping through contours, length " + str(len(cnts)));
	  for c in cnts:

	    # Grab size of contour:
	    # Can also consider using cv2.contourArea(cnt);
	    contour_area = Image_Utils.contour_bound_box_area(c);
	    contour_plot_size_fraction = contour_area/plot_area
	    contour_relative_size_fraction = contour_area/largest_contour_area;

	    Logger.get_logger().log_msg(Logger.DEBUG_FLAG_DEBUG, "Contour plot size fraction: " + str(contour_plot_size_fraction) + "; contour relative size fraction: " + str(contour_relative_size_fraction));

	    # if the contour is too small, draw it on the mask
	    if (contour_plot_size_fraction < global_threshold or contour_relative_size_fraction < relative_threshold):
	      Logger.get_logger().log_msg(Logger.DEBUG_FLAG_DEBUG, "Found a small contour, masking out");
	      contours_to_mask.append(c);

	  cv2.drawContours(mask, contours_to_mask, -1, 0, -1)

	  # remove the contours from the image
	  image = cv2.bitwise_not(cv2.bitwise_and(image_temp, image_temp, mask=mask));

	  return image;


	###############################################################################
	# Given a image, determines width of axis (assume crosshairs plot centered in image)
	# Assumes image is black and white binarized
	@staticmethod
	def measure_plot_axis_width(image, is_x_axis):

		# For readability, grab our height/width:
		plot_width = np.size(image, 1)
		plot_height = np.size(image, 0)

		if (is_x_axis):
			lower_point = int(plot_width/3);

		else:
			lower_point = int(plot_height/3);

		upper_point = lower_point*2;

		lower_axis_width = 0;
		upper_axis_width = 0;


		# Lower side First
		while (True):

			lower_point_low = 255
			upper_point_low = 255

			if (is_x_axis):
				lower_point_low = image[int(plot_height/2)-lower_axis_width, lower_point]
				upper_point_low = image[int(plot_height/2)-lower_axis_width, upper_point]

			else:
				lower_point_low = image[lower_point, int(plot_width/2)-lower_axis_width]
				upper_point_low = image[upper_point, int(plot_width/2)-lower_axis_width]

			if ((lower_point_low == 0) and (upper_point_low == 0)):
				lower_axis_width = lower_axis_width+1;
			else:
				break;


		# Then upper side:

		while (True):

			lower_point_high = 255
			upper_point_high = 255

			if (is_x_axis):
				lower_point_high = image[int(plot_height/2)+upper_axis_width,lower_point]
				upper_point_high = image[int(plot_height/2)+upper_axis_width,upper_point]

			else:
				lower_point_high = image[lower_point, int(plot_width/2)+upper_axis_width]
				upper_point_high = image[upper_point, int(plot_width/2)+upper_axis_width]


			if ((lower_point_high == 0) and (upper_point_high == 0)):
				upper_axis_width = upper_axis_width+1;
			else:
				break;

		return lower_axis_width, upper_axis_width;
