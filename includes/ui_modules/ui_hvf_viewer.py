###############################################################################
# ui_hvf_viewer.py
#
# Description:
#	UI definition for HVF viewer
#
# Main usage:
#
#	To Do:
#
###############################################################################

# For general purpose logging
from includes.utilities.logger import Logger;

from includes.utilities.file_utils import File_Utils;

from includes.hvf_data.hvf_object import Hvf_Object;

from includes.hvf_manager_hvf_editor import Hvf_Editor;



class Ui_Hvf_Viewer(tk.Frame):


	############################################################################
	# STATIC VARIABLES #########################################################
	############################################################################

    hvf_obj_dict = {};



    ############################################################################
	# INIT FUNCTIONS ###########################################################
	############################################################################

    def __init__(self, master=None):
        tk.Frame.__init__(self, master);
        self.grid();

        self.patient_list_box_title = StringVar();
        self.patient_list_box_title.set("Patient List");

        self.hvf_list_box_title = StringVar();

        self.hvf_list_box_title.set("HVF List");

        self.createWidgets()

    def createWidgets(self):

        row_cnt = 0

        self.select_hvf_file_button = tk.Button(self, text='Add HVF from text file', command=self.button_add_hvf_file)
        self.select_hvf_file_button.grid(row=row_cnt,column=0)

        row_cnt = row_cnt+1;

        self.select_hvf_dir_button = tk.Button(self, text='Add HVFs from directory', command=self.button_add_hvf_dir)
        self.select_hvf_dir_button.grid(row=row_cnt,column=0)

        row_cnt = row_cnt+1;

        self.patient_list_box_label = tk.Label(self, textvariable = self.patient_list_box_title)
        self.patient_list_box_label.grid(row=row_cnt,column=0)

        row_cnt = row_cnt+1;

        self.patient_list_box = tk.Listbox(self);
        self.patient_list_box.grid(row=row_cnt, column=0);

        row_cnt = row_cnt+1;

        self.hvf_list_box_label = tk.Label(self, textvariable = self.hvf_list_box_title)
        self.hvf_list_box_label.grid(row=row_cnt,column=0)

        row_cnt = row_cnt+1;

        self.hvf_file_list_box = tk.Listbox(self);
        self.hvf_file_list_box.grid(row=row_cnt, column=0);

        row_cnt = row_cnt+1;


    ############################################################################
	# UI FUNCTIONS #############################################################
	############################################################################

    def display_patient_list(hvf_obj_dict):

        # Clear all items

        # for each hvf key, add to list
        #for key in hvf_obj_dict.keys():

        return;    


    ############################################################################
    # BUTTON RECEIVER FUNCTIONS ################################################
    ############################################################################

	def button_add_hvf_file(self):
		initial_dir = os.getcwd();
		hvf_file = filedialog.askopenfilename(initialdir = initial_dir, title = "Select HVF file", filetypes = (("HVF text files","*.txt"),("all files","*.*")))

		if csv_file:
			self.add_hvf_file(hvf_file);

	def button_add_hvf_dir(self):
		initial_dir = os.getcwd();
		src_dir = filedialog.askdirectory(initialdir = initial_dir,title = "Select Directory of HVF files")

		if src_dir:
			self.add_hvf_directory(src_dir)

    ############################################################################
    # FILE READING FUNCTIONS ###################################################
    ############################################################################

    ############################################################################
    # Adds HVF text file to list
    def add_hvf_file(file_path):

        hvf_string = File_Utils.read_text_from_file(file_path);

        hvf_obj = Hvf_Object.get_hvf_object_from_text(hvf_string);

        Ui_Hvf_Viewer.hvf_obj_dict = Ui_Hvf_Viewer.add_hvf_to_display_dict(hvf_obj, Ui_Hvf_Viewer.hvf_obj_dict);

        return;

    ############################################################################
    # Adds HVF text files within a specified directory path
    def add_hvf_directory(dir_path):

        list_of_paths = File_Utils.get_files_within_dir(dir_path, [".txt"]);

        for path in list_of_paths:
            Ui_Hvf_Viewer.add_hvf_file(path);

        return;

    ############################################################################
    # HELPER FUNCTIONS #########################################################
    ############################################################################

    ############################################################################
    # Adds HVF object to display dict, which groups by patient name/laterality
    # If patient/laterality doesn't exist, makes a new group and adds HVF
    def add_hvf_to_display_dict(hvf_obj, display_dict):

        for dict_key in display_dict.keys():
            rep_hvf_obj = display_dict[dict_key][0];

            rep_laterality = rep_hvf_obj.metadata.get(HVF_Object.KEYLABEL_LATERALITY)
            hvf_obj_laterality = hvf_obj.metadata.get(HVF_Object.KEYLABEL_LATERALITY)

            if (Hvf_Editor.is_same_patient(hvf_obj, rep_hvf_obj) and (hvf_obj_laterality == rep_laterality)):
                # insert the hvf_object into the list, test date order
                # TODO: deal with test date parsing

                display_dict[dict_key].append(hvf_obj);


        # The hvf_obj is not in the list. Make a new key, and a generate a new list
        hvf_name = hvf_obj.metadata.get(HVF_Object.KEYLABEL_NAME);
        hvf_id = hvf_obj.metadata.get(HVF_Object.KEYLABEL_ID);
        hvf_laterality = hvf_obj.metadata.get(HVF_Object.KEYLABEL_LATERALITY);
        new_key = hvf_name + " " + hvf_id + " " + hvf_laterality;

        list = [hvf_obj]

        display_dict[new_key] = list;


        return display_dict;
