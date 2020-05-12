###############################################################################
# file_utils.py
#
# Description:
#	Class definition for commonly used, general use file handling functions
#
###############################################################################

# Import necessary packages
import sys
import os
import cv2
from shutil import copyfile
import pydicom

class File_Utils:
	###############################################################################
	# CONSTANTS AND STATIC VARIABLES ##############################################
	###############################################################################

	###############################################################################
	# FILE I/O METHODS ############################################################
	###############################################################################

    ###############################################################################
    # Given directory path and list of extensions, gets all files within directory
    # with that extensions and returns in list.
    # Returns full paths
    # Does not recursively walk subdirectories
    @staticmethod
    def get_files_within_dir(dir_path, list_of_exts):

        file_list = [];

    	# For each file in the test folder:
        for file_name in os.listdir(dir_path):

            full_file_name_path = os.path.join(dir_path, file_name)
            if os.path.isfile(full_file_name_path):

                # Skip hidden files:
                if file_name.startswith('.'):
                    continue;

                # Then, find corresponding serialization text file
                filename_root, ext = os.path.splitext(file_name);

                # If file has appropriate extension, add to return list
                if (ext.lower() in list_of_exts):
                    file_list.append(full_file_name_path);

        return file_list;

    ###############################################################################
    # Given directory path, gets all immediate subdirectories and returns as list
    # Returns full paths
    # Does not recursively walk subdirectories
    @staticmethod
    def get_dirs_within_dir(dir_path):

        dir_list = [];

    	# For dir  in the test folder:
        for dir_name in os.listdir(dir_path):

            # If indeed directory, add to list
            full_dir_name_path = os.path.join(dir_path, dir_name)
            if os.path.isdir(full_dir_name_path):

                dir_list.append(dir_name)

        return dir_list;


    ###############################################################################
    # Given file path, reads cv2 image from file
    @staticmethod
    def read_image_from_file(file_path):

        return cv2.imread(file_path);

    ###############################################################################
    # Given file path, reads DICOM object from file
    @staticmethod
    def read_dicom_from_file(file_path):

        return pydicom.dcmread(file_path);

    ###############################################################################
    # Given directory path, reads cv2 images from all files within the directory
    # Does not recursively search for files within any subdirectories
    # Returns a dictionary with file_name root -> image
    @staticmethod
    def read_images_from_directory(dir_path):

        list_of_image_file_extensions = [".bmp", ".jpg", ".jpeg", ".png"];

        files_to_read = File_Utils.get_files_within_dir(dir_path, list_of_image_file_extensions);

        return_dict = {};
        for file_path in files_to_read:

            head, file_name = os.path.split(file_path);

            return_dict[file_name] = File_Utils.read_image_from_file(file_path)

        return return_dict;

    ###############################################################################
    # Given file path, reads in content as string and returns it
    @staticmethod
    def read_text_from_file(file_path):
        f = open(file_path, "r");
        text_string = f.read();
        f.close();
        return text_string;

    ###############################################################################
    # Given directory path, reads content from all files within the directory
    # Does not recursively search for files within any subdirectories
    # Returns a dictionary with file_name root -> text string
    @staticmethod
    def read_texts_from_directory(dir_path):

        list_of_text_file_extensions = [".txt"];

        files_to_read = File_Utils.get_files_within_dir(dir_path, list_of_text_file_extensions);

        return_dict = {};
        for file_path in files_to_read:

            head, file_name = os.path.split(file_path);

            return_dict[file_name] = File_Utils.read_text_from_file(file_path)

        return return_dict

    ###############################################################################
    # Given string and path, write string to path filename
    @staticmethod
    def write_string_to_file(content_string, file_path):

        f = open(file_path, "w+");
        f.write(content_string);
        f.close();
        return "";

    ###############################################################################
    # Given dictionary of file_name->strings and directory path, writes each string
    # to a separate file
    @staticmethod
    def write_strings_to_directory_files(dict_of_strings, dir_path):

        # Write each string individually
        for file_name in dict_of_strings:

            # Construct the file name:
            file_path = os.path.join(dir_path, str(file_name)+".txt");

            # Write file:
            File_Utils.write_string_to_file(dict_of_strings[file_name], file_path);


        return "";



	###############################################################################
	# FILE HANDLER METHODS ########################################################
	###############################################################################


    ###############################################################################
    # Gets a file handle (for easy file writing)
    @staticmethod
    def get_writing_fh(file_path):
        fh = open(file_path, "w+");



    ###############################################################################
    # Writes a line to the file handler
    @staticmethod
    def write_fh_line(fh, string_content):
        fh.write(string_content);

    ###############################################################################
    # Closes a file handler
    @staticmethod
    def close_fh(fh):
        fh.close();
