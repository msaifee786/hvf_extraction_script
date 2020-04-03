#!/usr/bin/env python
###############################################################################
# hvf_image_extractor_ui.py
#
# Description:
#	UI code for HVF Image Extractor
#
#
#
###############################################################################


# Import necessary packages
import sys;
import argparse;
from shutil import copyfile
import os
import re
import shutil

import tkinter as tk
from tkinter import filedialog
from tkinter import StringVar
from tkinter import IntVar

from tkinter import ttk
from ttk import Treeview

from includes.hvf_data.hvf_object import Hvf_Object
from includes.utilties.file_utils import File_Utils

class Application(tk.Frame):

	###############################################################################
	# CONSTANTS AND STATIC VARIABLES ##############################################
	###############################################################################
	INITIAL_DIR = os.getcwd()

	# For TreeView list of HVFs:
	LIST_OF_HVF_HEADERS = [
		Hvf_Object.KEYLABEL_NAME,
		Hvf_Object.KEYLABEL_ID,
		Hvf_Object.KEYLABEL_TEST_DATE,
		Hvf_Object.KEYLABEL_LATERALITY,
		Hvf_Object.KEYLABEL_FIELD_SIZE
	];


	def __init__(self, master=None):
		tk.Frame.__init__(self, master);
		self.grid();

		# Declare object vars:
		self.list_of_hvfs = [];


		# First, create our master grid:
		self.master_frame = tk.Frame(self);
		self.master_frame.grid();


		# Next, make our subframes:

		# Top HVF object management frame:
		self.hvf_obj_management_frame = tk.Frame(self.master_frame);
		self.hvf_obj_management_frame.grid(row=0, column=0);

		# Within our management frame, make our individual frames

		# Import button frame, with all of its buttons:
		self.import_button_frame = tk.Frame(self.hvf_obj_management_frame);
		self.import_button_frame.grid(row=0, column=0);

		self.load_image_file_button = tk.Button(self.import_button_frame, text="Load Image File", command=self.load_image_file)
		self.load_image_file_button.grid(row=0, column=0);

		self.load_image_directory_button = tk.Button(self.import_button_frame, text="Load Images from Directory", command=self.load_image_directory)
		self.load_image_directory_button.grid(row=1, column=0);

		self.load_text_file_button = tk.Button(self.import_button_frame, text="Load Text File", command=self.load_text_file)
		self.load_text_file_button.grid(row=2, column=0);

		self.load_text_directory_button = tk.Button(self.import_button_frame, text="Load Text Files from Directory", command=self.load_text_directory)
		self.load_text_directory_button.grid(row=3, column=0);


		# List of HVFs, with all of its items:

		self.list_of_hvf_frame = tk.Frame(self.hvf_obj_management_frame);
		self.list_of_hvf_frame.grid(row=0, column=1);

		self.hvf_list_tree = ttk.Treeview(self.list_of_hvf_frame);
		self.hvf_list_tree.grid(row=0, column=0)

		self.hvf_list_tree["columns"] = Application.LIST_OF_HVF_HEADERS;
		for ii in range(len(Application.LIST_OF_HVF_HEADERS)):
			self.hvf_list_tree.column(Application.LIST_OF_HVF_HEADERS[ii], width=75);
			self.hvf_list_tree.heading(Application.LIST_OF_HVF_HEADERS[ii], text=Application.LIST_OF_HVF_HEADERS[ii]);


		# HVF Viewer, with its label and stringvar:

		self.hvf_viewer_frame = tk.Frame(self.hvf_obj_management_frame);
		self.hvf_viewer_frame.grid(row=0, column=2);

		self.hvf_viewer_stringvar = StringVar();
		self.hvf_viewer_stringvar.set("No HVF selected");

		self.hvf_viewer_label = tk.Label(self.hvf_viewer_frame, textvariable=self.hvf_viewer_stringvar )
		self.hvf_viewer_label.grid(row=0, column=0)


		# Export button frame, with all of its buttons:

		self.export_button_frame = tk.Frame(self.hvf_obj_management_frame);
		self.export_button_frame.grid(row=0, column=3);

		self.export_text_files_button = tk.Button(self.export_button_frame, text="Export to Text Files", command=self.export_text_files)
		self.export_text_files_button.grid(row=0, column=0);

		self.export_spreadsheet_button = tk.Button(self.export_button_frame, text="Export to Spreadsheet", command=self.export_spreadsheet)
		self.export_spreadsheet_button.grid(row=1, column=0);


		# Bottom bulk metrics frame, with its stringvar
		self.bulk_metrics_frame = tk.Frame(self.master_frame);
		self.bulk_metrics_frame.grid(row=1, column=0);

		self.bulk_metrics_stringvar = StringVar();
		self.bulk_metrics_stringvar.set("No Bulk Metrics Calculated");
		self.bulk_metrics_label = tk.Label(self.bulk_metrics_frame, textvariable=self.bulk_metrics_stringvar)
		self.bulk_metrics_label.grid(row=0, column=0);



		# master Frame
		# hvf_obj_management_frame
		# 	import_button_frame
		# 		Load image file
		# 		Load image directory
		# 		Load text file
		# 		Load text directory
		#
		# 	list_of_hvf_frame
		#
		# 	hvf_viewer_frame
		# 		StringVar HVF
		#
		# 	export_button_frame
		# 		Export to text files
		# 		Export to spreadsheet
		# bulk_metrics_frame

	###############################################################################
	#
	def load_image_file(self):
		image_file_path = filedialog.askopenfilename(initialdir = Application.INITIAL_DIR, title = "Select Image File", filetypes = (("all files","*.*")))

		try:
			hvf_obj = Hvf_Object.get_hvf_object_from_image(File_Utils.read_image_from_file(image_file_path));
			self.list_of_hvfs.append(hvf_obj);
			self.refresh_hvf_list();

		except:
			print("Invalid image file selected");

		return;


	###############################################################################
	#
	def load_image_directory(self):
		image_dir_path = filedialog.askdirectory(initialdir = Application.INITIAL_DIR, title = "Select Image Directory")

		list_of_image_file_extensions = [".bmp", ".jpg", ".jpeg", ".png"];
		list_of_img_paths = File_Utils.get_files_within_dir(image_dir_path, list_of_image_file_extensions);


		for img_path in list_of_img_paths:

			try:

				hvf_obj = Hvf_Object.get_hvf_object_from_image(File_Utils.read_image_from_file(img_path));
				self.list_of_hvfs.append(hvf_obj);

			except:
				print("Unable to load image file: " + img_path);

		self.refresh_hvf_list();



		return;

	###############################################################################
	#
	def load_text_file(self):
		text_file_path = filedialog.askopenfilename(initialdir = Application.INITIAL_DIR, title = "Select text file", filetypes = (("text files","*.txt"),("all files","*.*")))
		text_string = File_Utils.read_text_from_file(text_file_path)
		hvf_obj = Hvf_Object.get_hvf_object_from_text(text_string)

		self.list_of_hvfs.append(hvf_obj);

		self.refresh_hvf_list();

		#try:


		#except:
		#	print("Invalid text file selected");

		return;

	###############################################################################
	#
	def load_text_directory(self):

		txt_dir_path = filedialog.askdirectory(initialdir = Application.INITIAL_DIR, title = "Select Text Directory")

		list_of_txt_file_extensions = [".txt"];
		list_of_txt_paths = File_Utils.get_files_within_dir(txt_dir_path, list_of_txt_file_extensions);


		for txt_path in list_of_txt_paths:

			try:

				hvf_obj = Hvf_Object.get_hvf_object_from_text(File_Utils.read_text_from_file(txt_path));
				self.list_of_hvfs.append(hvf_obj);

			except:
				print("Unable to load text file: " + txt_path);

		self.refresh_hvf_list();
		return;

	###############################################################################
	#
	def export_text_files(self):
		return;

	###############################################################################
	#
	def export_spreadsheet(self):
		return;

	###############################################################################
	# HELPER FUNCTIONS ############################################################
	###############################################################################

	###############################################################################
	#
	def refresh_hvf_list(self):

		self.hvf_list_tree.delete(*self.hvf_list_tree.get_children())

		list_of_headers = Application.LIST_OF_HVF_HEADERS.copy;

		for ii in range(len(self.list_of_hvfs)):

			hvf_obj = self.list_of_hvfs[ii];

			first_field = hvf_obj.metadata.get(list_of_headers.pop(0));

			other_fields = map(lambda x: hvf_obj.metadata.get(x), list_of_headers);

			self.hvf_list_tree.insert("", ii, "", text=first_field, values=other_fields)
		return;

app = Application()
app.master.title('HVF Image Extractor');
app.mainloop();
