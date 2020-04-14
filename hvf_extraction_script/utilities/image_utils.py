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
	