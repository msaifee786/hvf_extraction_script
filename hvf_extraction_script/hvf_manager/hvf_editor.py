###############################################################################
# hvf_editor.py
#
# Description:
#	Functions for editing HVF objects
#
###############################################################################

# Import necessary packages
import numpy as np
import copy

# Import logger class to handle any messages:
from hvf_extraction_script.utilities.logger import Logger;

# Import the HVF_Object class and helper classes
from hvf_extraction_script.hvf_data.hvf_object import Hvf_Object;
from hvf_extraction_script.hvf_data.hvf_plot_array import Hvf_Plot_Array
from hvf_extraction_script.hvf_data.hvf_perc_icon import Hvf_Perc_Icon
from hvf_extraction_script.hvf_data.hvf_value import Hvf_Value

class Hvf_Editor:

	###############################################################################
	# VARIABLE/CONSTANT DECLARATIONS: #############################################
	###############################################################################

	###############################################################################
	# STATIC EDITING FUNCTIONS ####################################################
	###############################################################################

	###############################################################################
	# Converts HVF object from 30-2 to 24-2. If it is not 30-2, does nothing.
	@staticmethod
	def convert_hvf_302_to_242(hvf_obj):
		if (hvf_obj.metadata.get(Hvf_Object.KEYLABEL_FIELD_SIZE) == Hvf_Object.HVF_30_2):

			is_right = hvf_obj.metadata.get(Hvf_Object.KEYLABEL_LATERALITY) == Hvf_Object.HVF_OD;

			hvf_obj.raw_value_array = Hvf_Editor.mask_302_to_242(hvf_obj.raw_value_array, is_right);
			hvf_obj.abs_dev_value_array = Hvf_Editor.mask_302_to_242(self.abs_dev_value_array, is_right);
			hvf_obj.pat_dev_value_array = Hvf_Editor.mask_302_to_242(self.pat_dev_value_array, is_right);
			hvf_obj.abs_dev_percentile_array = Hvf_Editor.mask_302_to_242(self.abs_dev_percentile_array, is_right);
			hvf_obj.pat_dev_percentile_array = Hvf_Editor.mask_302_to_242(self.pat_dev_percentile_array, is_right);

		return;

	###############################################################################
	# GENERAL PURPOSE ARRAY METHODS ###############################################
	###############################################################################

	###############################################################################
	# For transposing left -> right eye arrays
	def transpose_array(array):

		new_array = array.copy();

		for i in range(0, np.size(array, 1)):

			size = np.size(array, 0)

			for j in range(0, size):

				new_array[j,i] = array[size-1-j,i]

		return new_array;

	###############################################################################
	# For converting 30-2 fields to 24-2
	# also takes in flag for is_right indicating if right eye (false if left) -
	# needed for transposition
	def mask_302_to_242(plot_obj, is_right):

		new_plot_obj = copy.deepcopy(plot_obj);

		# Transpose the array if needed:
		if not is_right:
			new_plot_obj.plot_array = Hvf_Editor.transpose_array(new_plot_obj.plot_array);

		# Iterate through the array:
		for i in range(0, np.size(new_plot_obj.plot_array, 1)):
			size = np.size(new_plot_obj.plot_array, 0)
			for j in range(0, size):

				if not (Hvf_Plot_Array.BOOLEAN_MASK_24_2[j][i]):
					if (new_plot_obj.icon_type == Hvf_Plot_Array.PLOT_PERC):
						new_plot_obj.plot_array[j,i] = Hvf_Perc_Icon.get_perc_icon_from_char(Hvf_Perc_Icon.PERC_NO_VALUE_CHAR);
					elif (new_plot_obj.icon_type == Hvf_Plot_Array.PLOT_VALUE):
						new_plot_obj.plot_array[j,i] = Hvf_Value.get_value_from_display_string(Hvf_Value.VALUE_NO_VALUE_CHAR);

		# Transpose the array back if needed:
		if not is_right:
			new_plot_obj.plot_array = Hvf_Editor.transpose_array(new_plot_obj.plot_array);

		return new_plot_obj;
