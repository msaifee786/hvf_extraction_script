###############################################################################
# hvf_metric_calculator.py
#
# Description:
#	Functions for calculating global and regional metrics of an HVF_Object.
#   Meant to be used as static methods (no need to instantiate calculator obj)
#
#	These functions assume a 24-2 field size. Any 30-2 HVF objects will be
#	converted (masked) into 24-2. This function will produce erroneous metrics
#	for 10-2.
#
###############################################################################

# Import necessary packages
import numpy as np

import pprint

# Import logger class to handle any messages:
from hvf_extraction_script.utilities.logger import Logger;

# Import the HVF_Object class and helper classes
from hvf_extraction_script.hvf_data.hvf_object import Hvf_Object;
from hvf_extraction_script.hvf_data.hvf_perc_icon import Hvf_Perc_Icon;
from hvf_extraction_script.hvf_data.hvf_value import Hvf_Value;
from hvf_extraction_script.hvf_data.hvf_plot_array import Hvf_Plot_Array

# Import HVF data managers:
from hvf_extraction_script.hvf_manager.hvf_editor import Hvf_Editor;


class Hvf_Metric_Calculator:

	###############################################################################
	# VARIABLE/CONSTANT DECLARATIONS: #############################################
	###############################################################################

	###############################################################################
	# 2D array specifying individual regions within a 24-2 field. This mask is for
	# a RIGHT eye (must be transposed for left).
	#
	# Pattern follows:
	#       4 4 | 6 6
	#     4 4 4 | 4 6 6
	#   8 8 2 2 | 2 2 x x
	# 8 8 8 0 0 | 0 x   x
	# ---------------------
	# 9 9 9 1 1 | 1 x   x
	#   9 9 3 3 | 3 3 x x
	#     5 5 5 | 5 7 7
	#       5 5 | 7 7
	#
	# Labels (superior/inferior):
	#	0, 1 - Central
	#	2, 3 - Paracentral
	#	4, 5 - Arcuate 1
	#	6, 7 - Arcuate 2
	#	8, 9 - Nasal
	REGION_NUMERICAL_MASK = [
		['x', 'x', 'x', 'x', 'x', 'x', 'x', 'x', 'x', 'x'],
		['x', 'x', 'x',  4,   4,   6,   6,  'x', 'x', 'x'],
		['x', 'x',  4,   4,   4,   4,   6,   6,  'x', 'x'],
		['x',  8,   8,   2,   2,   2,   2,  'x', 'x', 'x'],
		[ 8,   8,   8,   0,   0,   0,  'x', 'x', 'x', 'x'],
		[ 9,   9,   9,   1,   1,   1,  'x', 'x', 'x', 'x'],
		['x',  9,   9,   3,   3,   3,   3,  'x', 'x', 'x'],
		['x', 'x',  5,   5,   5,   5,   7,   7,  'x', 'x'],
		['x', 'x', 'x',  5,   5,   7,   7,  'x', 'x', 'x'],
		['x', 'x', 'x', 'x', 'x', 'x', 'x', 'x', 'x', 'x']
	];

	NUMBER_REGIONS = 10;

	###############################################################################
	# CIGTS SCORING CONSTANTS:

	CIGTS_ICON_SCORE = {
		Hvf_Perc_Icon.PERC_NORMAL: 0,
		Hvf_Perc_Icon.PERC_5_PERCENTILE: 1,
		Hvf_Perc_Icon.PERC_2_PERCENTILE: 2,
		Hvf_Perc_Icon.PERC_1_PERCENTILE: 3,
		Hvf_Perc_Icon.PERC_HALF_PERCENTILE: 4
	};

	###############################################################################
	# SIMPLE METRIC FUNCTIONS #####################################################
	###############################################################################

    ###############################################################################
    # Calculates VFI score
	def get_vfi_score(hvf_obj):

		return 0;

	###############################################################################
	# Calculates regional total deviation score
	def get_regional_total_deviation(hvf_obj):

		return 0;

	###############################################################################
	# Calculates regional pattern deviation score
	def get_regional_pattern_deviation(hvf_obj):

		return 0;

	###############################################################################
	# CIGTS METRIC FUNCTIONS ######################################################
	###############################################################################

	# Based on CIGTS trial. Calculation algorithm based on paper:
	# The Collaborative Initial Glaucoma Treatment Study: Baseline Visual Field
	# and Test-Retest Variability

	###############################################################################
	# Calculates global CIGTS TDP score
	def get_global_cigts_tdp_score(hvf_obj):

		# Grab the plot_object, and a few pertinent metadata
		plot_obj = hvf_obj.abs_dev_percentile_array;
		is_right = hvf_obj.metadata.get(Hvf_Object.KEYLABEL_LATERALITY) == Hvf_Object.HVF_OD;

		# Mask to 24-2 if necessary:
		if (hvf_obj.metadata.get(Hvf_Object.KEYLABEL_FIELD_SIZE) == Hvf_Object.HVF_30_2):
			Hvf_Editor.mask_302_to_242(plot_obj, is_right);

		# Now take the perc_array:
		perc_array = plot_obj.plot_array;

		# If left, need to transpose:
		if not is_right:
			perc_array = Hvf_Editor.transpose_array(perc_array);

		cigts_score_array = Hvf_Metric_Calculator.calculate_cigts_score_array(perc_array);

		return int(np.sum(cigts_score_array)/10.4)

	###############################################################################
	# Calculates global CIGTS PDP score
	def get_global_cigts_pdp_score(hvf_obj):

		# Grab the plot_object, and a few pertinent metadata
		plot_obj = hvf_obj.pat_dev_percentile_array;
		is_right = hvf_obj.metadata.get(Hvf_Object.KEYLABEL_LATERALITY) == Hvf_Object.HVF_OD;

		# Mask to 24-2 if necessary:
		if (hvf_obj.metadata.get(Hvf_Object.KEYLABEL_FIELD_SIZE) == Hvf_Object.HVF_30_2):
			Hvf_Editor.mask_302_to_242(plot_obj, is_right);

		# Now take the perc_array:
		perc_array = plot_obj.plot_array;

		# If left, need to transpose:
		if not is_right:
			perc_array = Hvf_Editor.transpose_array(perc_array);

		cigts_score_array = Hvf_Metric_Calculator.calculate_cigts_score_array(perc_array);

		return int(np.sum(cigts_score_array)/10.4)


	###############################################################################
	# Calculates regional CIGTS TDP score
	def get_regional_cigts_tdp_score(hvf_obj):

		return 0;

	###############################################################################
	# Calculates regional CIGTS PDP score
	def get_regional_cigts_pdp_score(hvf_obj):

		return 0;


	###############################################################################
	# Helper function - calculates CIGTS score for input percentile array
	# NOTE: calculates raw scores in array layout (10x10), to be summed by
	# calling function
	def calculate_cigts_score_array(perc_array):

		cigts_score = 0;
		cigts_score_array = np.zeros(np.shape(perc_array));

		# Iterate through entire array:
		for y in range(0, np.size(perc_array, 0)):
			for x in range(0, np.size(perc_array, 1)):

				# Grab the icon:
				element = perc_array[x, y].get_enum()

				# Move on if element is not a true icon, or if its normal
				if ((element == Hvf_Perc_Icon.PERC_NORMAL) or not (element in Hvf_Metric_Calculator.CIGTS_ICON_SCORE.keys())):
					continue;

				# Initialize counts of surrounding icons:
				icon_counter_dict = {
					Hvf_Perc_Icon.PERC_NORMAL: 0,
					Hvf_Perc_Icon.PERC_5_PERCENTILE: 0,
					Hvf_Perc_Icon.PERC_2_PERCENTILE: 0,
					Hvf_Perc_Icon.PERC_1_PERCENTILE: 0,
					Hvf_Perc_Icon.PERC_HALF_PERCENTILE: 0
					};

				# Iterate through all surrounding icons
				# We'll also iterate through icon itself, as its easier (delete it later)
				for jj in range(y-1, y+2):
					for ii in range(x-1, x+2):

						# Move on if out of bounds:
						if ((jj < 0 or jj >= np.size(perc_array, 0)) or (ii < 0 or ii >= np.size(perc_array, 1))):
							continue;

						# Get adjacent element enum:
						adj_element_enum = perc_array[ii, jj].get_enum()

						# Move on if adjacent icon is not a true icon:
						if not (adj_element_enum in Hvf_Metric_Calculator.CIGTS_ICON_SCORE.keys()):
							continue;

						# Skip if not in same vertical hemisphere:
						if (((y == 4) and (jj == 5)) or ((y == 5) and (jj == 4))):
							continue;

						# Add icon count:
						icon_counter_dict[adj_element_enum] = icon_counter_dict[adj_element_enum]+1;

				# Lastly, loop above counted cell of interest, so need to remove:
				icon_counter_dict[element] = icon_counter_dict[element]-1

				# Determine max adjacent depth (with count 2+):
				max_adjacent_depth = Hvf_Perc_Icon.PERC_NORMAL;

				for icon in icon_counter_dict.keys():
					if ((icon_counter_dict[icon] >= 2) and (Hvf_Metric_Calculator.CIGTS_ICON_SCORE[icon] > Hvf_Metric_Calculator.CIGTS_ICON_SCORE[max_adjacent_depth])):
						max_adjacent_depth = icon;

				# Now, taken the minimum between the adjacent icon score and the element score:
				element_cigts_score = min(Hvf_Metric_Calculator.CIGTS_ICON_SCORE[element], Hvf_Metric_Calculator.CIGTS_ICON_SCORE[max_adjacent_depth]);
				cigts_score = cigts_score + element_cigts_score
				cigts_score_array[x, y] = element_cigts_score


		# Now, normalize the score:
		cigts_score = int(cigts_score/10.4)


		# for y in range(0, np.size(cigts_score_array, 0)):
		# 	line_string = "";
		# 	for x in range(0, np.size(cigts_score_array, 1)):
		#
		# 		element = int(cigts_score_array[x, y])
		#
		# 		if (element == 0):
		# 			element = "  ";
		# 		elif (element == -1):
		# 			element = str(element);
		# 		else:
		# 			element = " "+str(element)
		#
		# 		line_string = line_string + element + "|"
		#
		# 	print(line_string);

		# Return array (calling function will sum up as needed)
		return cigts_score_array;

	###############################################################################
	# AGIS METRIC FUNCTIONS #######################################################
	###############################################################################

    ###############################################################################
    # Calculates global AGIS score
	def get_global_agis_score(hvf_obj):

		return 0;

    ###############################################################################
    # Calculates regional AGIS score
	def get_regional_agis_score(hvf_obj):

		return 0;

	###############################################################################
	# HELPER METRIC FUNCTIONS #####################################################
	###############################################################################

	###############################################################################
	# Mask for particular region (and deletes all else), based on input argument:
	# Assumes right eye format
	# Does no error checking on region_val
	def mask_field_region(perc_array, icon_type, region_val):

		ret_perc_array = perc_array.copy();

		# Iterate through entire array:
		for y in range(0, np.size(perc_array, 0)):
			for x in range(0, np.size(perc_array, 1)):

				if not (Hvf_Metric_Calculator.REGION_NUMERICAL_MASK[x, y] == region_val):
					if (icon_type == Hvf_Plot_Array.PLOT_VALUE):
						ret_perc_array[x, y] = Hvf_Value.get_value_from_display_string("");
					if (icon_type == Hvf_Plot_Array.PLOT_PERC):
						ret_perc_array[x, y] = Hvf_Perc_Icon.get_perc_icon_from_char(" ")

		return ret_perc_array;
