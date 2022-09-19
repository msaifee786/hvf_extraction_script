###############################################################################
# ocr_utils.py
#
# Description:
# 	Class definition for OCR utility functions
#
###############################################################################

# Import necessary packages

# Import OCR packages
# import locale

# locale.setlocale(locale.LC_ALL, "C")
# import tesserocr

# General purpose image functions:
from hvf_extraction_script.utilities.image_utils import Image_Utils
from hvf_extraction_script.utilities.regex_utils import Regex_Utils

# Import necessary image packages:
from PIL import Image
from tesserocr import PSM, PyTessBaseAPI


class Ocr_Utils:
    ###############################################################################
    # CONSTANTS AND STATIC VARIABLES ##############################################
    ###############################################################################

    OCR_API_HANDLE = None

    ###############################################################################
    # OCR METHODS #################################################################
    ###############################################################################

    ###############################################################################
    # Given an image, preprocesses it and pulls OCR text out of it
    # Uses pytesseract. Assumes input is in a Numpy/openCV image format
    @staticmethod
    def perform_ocr(img, proc_img: bool = True, debug_dir: str = "") -> str:

        if proc_img:
            # First, preprocessor the image:
            img = Image_Utils.preprocess_image(img, debug_dir=debug_dir)

        # Next, convert image to python PIL (because pytesseract using PIL):
        img_pil = Image.fromarray(img)

        if not Ocr_Utils.OCR_API_HANDLE:
            Ocr_Utils.OCR_API_HANDLE = PyTessBaseAPI(psm=PSM.SINGLE_COLUMN)
            # Ocr_Utils.OCR_API_HANDLE = PyTessBaseAPI(psm=PSM.SINGLE_BLOCK)

        Ocr_Utils.OCR_API_HANDLE.SetImage(img_pil)
        Ocr_Utils.OCR_API_HANDLE.SetSourceResolution(200)
        text: str = Ocr_Utils.OCR_API_HANDLE.GetUTF8Text()

        if debug_dir:
            out = Regex_Utils.temp_out(debug_dir=debug_dir)
            img_pil.save(f"{out}.jpg")
            with open(f"{out}.txt", "w") as f:
                f.writelines(text)

        # Return extracted text:
        return text
