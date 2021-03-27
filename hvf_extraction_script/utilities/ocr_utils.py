###############################################################################
# ocr_utils.py
#
# Description:
#	Class definition for OCR utility functions
#
###############################################################################

# Import necessary packages

# Import OCR packages
import locale
locale.setlocale(locale.LC_ALL, 'C')
import tesserocr
from tesserocr import PyTessBaseAPI
from tesserocr import PSM

# Import necessary image packages:
from PIL import Image

# General purpose image functions:
from hvf_extraction_script.utilities.image_utils import Image_Utils


class Ocr_Utils:
	###############################################################################
	# CONSTANTS AND STATIC VARIABLES ##############################################
	###############################################################################

    OCR_API_HANDLE = None;

	###############################################################################
	# OCR METHODS #################################################################
	###############################################################################

	###############################################################################
	# Given an image, preprocesses it and pulls OCR text out of it
	# Uses pytesseract. Assumes input is in a Numpy/openCV image format
    @staticmethod
    def perform_ocr(img):

		# First, preprocessor the image:
        img = Image_Utils.preprocess_image(img);

		# Next, convert image to python PIL (because pytesseract using PIL):
        img_pil = Image.fromarray(img);

        if not Ocr_Utils.OCR_API_HANDLE:
            Ocr_Utils.OCR_API_HANDLE = PyTessBaseAPI(psm=PSM.SINGLE_COLUMN)
            #Ocr_Utils.OCR_API_HANDLE = PyTessBaseAPI(psm=PSM.SINGLE_BLOCK)

        Ocr_Utils.OCR_API_HANDLE.SetImage(img_pil);
        text = Ocr_Utils.OCR_API_HANDLE.GetUTF8Text();

		# Return extracted text:
        return text;
