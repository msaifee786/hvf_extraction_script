###############################################################################
# hvf_patient_container.py
#
# Description:
#	Class description for container to hold HVFs, grouped by patient/laterality
#	Organizes HVFs by:
#		Patient
#			Laterality
#				HVF (ordered by date)
###############################################################################

# Import necessary packages
import numpy as np

# Import logger class to handle any messages:
from hvf_extraction_script.utilities.logger import Logger;

# Import the HVF_Object class:
from hvf_extraction_script.hvf_data.hvf_object import Hvf_Object;

class Hvf_Patient_Container:

	###############################################################################
	# VARIABLE/CONSTANT DECLARATIONS: #############################################
	###############################################################################

	###############################################################################
	# INIT/OBJECT FUNCTIONS #######################################################
	###############################################################################

	###############################################################################
	# Initialization function:
	def __init__(self):
		self.hvf_obj_dict = {};

	###############################################################################
	# Add new patient to list:
	def add_hvf(self, hvf_obj):

		# Construct a few parameters of hvf_obj to help organize/sorting:
		hvf_obj_patient_id = hvf_obj.metadata.get(Hvf_Object.KEYLABEL_NAME).lower() + " | " + hvf_obj.metadata.get(Hvf_Object.KEYLABEL_ID)

		hvf_obj_laterality = hvf_obj.metadata.get(Hvf_Object.KEYLABEL_LATERALITY);

		hvf_obj_date_key = hvf_obj.metadata.get(Hvf_Object.KEYLABEL_TEST_DATE);

		# First, is patient present in this container? If its not, add patient in
		if not (hvf_obj_patient_id in self.hvf_obj_dict):
			self.hvf_obj_dict[hvf_obj_patient_id] = {};

		# Now, we know patient is present. Is laterality present? If not, add it in
		if not (hvf_obj_laterality in self.hvf_obj_dict[hvf_obj_patient_id]):
			self.hvf_obj_dict[hvf_obj_patient_id][hvf_obj_laterality] = {};

		# Lastly, add in HVF object:

		self.hvf_obj_dict[hvf_obj_patient_id][hvf_obj_laterality][hvf_obj_date_key] = hvf_obj

		return;

	###############################################################################
	# Get list of patients in this container:
	def get_patient_list(self):
		return self.hvf_obj_dict.keys();


	###############################################################################
	# Get list of lateralities for a particular patient:
	def get_laterality_list(self, patient_id):
		return self.hvf_obj_dict.get(patient_id, {}).keys();


	###############################################################################
	# Get dictionary of test dates -> hvf_objs for a particular patient/laterality:
	def get_hvf_obj_dict(self, patient_id, laterality):
		return self.hvf_obj_dict.get(patient_id, {}).get(laterality, {});


	###############################################################################
	# Remove an HVF from the container. Must pass in the object to remove
	# Assumes hvf_obj is in container
	def remove_hvf(self, hvf_obj):

		# Construct a few parameters of hvf_obj to help organize/sorting:
		hvf_obj_patient_id = hvf_obj.metadata.get(Hvf_Object.KEYLABEL_NAME).lower() + " | " + hvf_obj.metadata.get(Hvf_Object.KEYLABEL_ID)

		hvf_obj_laterality = hvf_obj.metadata.get(Hvf_Object.KEYLABEL_LATERALITY);

		hvf_obj_date_key = hvf_obj.metadata.get(Hvf_Object.KEYLABEL_TEST_DATE);


		self.remove_hvf_by_parameter(hvf_obj_patient_id, hvf_obj_laterality, hvf_obj_date_key);

		return;

	###############################################################################
	# Remove an HVF from the container using parameters.
	# Assumes hvf_obj is in container
	def remove_hvf_by_parameter(self, id, laterality, date_key):

		# First, pop/remove the hvf
		self.hvf_obj_dict.get(id, {}).get(laterality, {}).pop(date_key, None);

		# Then clean up laterality/id if there are no other elements:
		if not (self.hvf_obj_dict.get(id, {}).get(laterality, {})):
			self.hvf_obj_dict.get(id, {}).pop(laterality, None);

		if not (self.hvf_obj_dict.get(id, {})):
			self.hvf_obj_dict.pop(id, None);

		return;

	###############################################################################
	# NON-EDITING HELPER FUNCTIONS ################################################
	###############################################################################

	@staticmethod
	def is_same_patient(hvf_obj1, hvf_obj2):

		name_bool = hvf_obj1.metadata.get(HVF_Object.KEYLABEL_NAME).lower() == hvf_obj2.metadata.get(HVF_Object.KEYLABEL_NAME).lower()

		id_bool = hvf_obj1.metadata.get(HVF_Object.KEYLABEL_ID) == hvf_obj2.metadata.get(HVF_Object.KEYLABEL_ID)

		dob_bool = hvf_obj1.metadata.get(HVF_Object.KEYLABEL_DOB) == hvf_obj2.metadata.get(HVF_Object.KEYLABEL_DOB)

		return (name_bool and id_bool and dob_bool)
