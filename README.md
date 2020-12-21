# HVF Extraction Script

Python module for Humphrey Visual Field (HVF) report data extraction. Extracts data using OCR (tesseract) and image processing techniques (openCV) to extract data into an object oriented format for further processing.

## Getting Started

### Requirements
- Python 3.6.7 or higher
- TesserOCR
- Regex
- PyDicom
- Pillow
- OpenCV 4.2.0
- FuzzyWuzzy
- Fuzzysearch

### Installation

Note: This software package was developed and tested on an Intel Mac OSX system; while it should work on any platform, its execution is best understood on such systems.

To use the system, first download and install [Anaconda](https://www.anaconda.com/) (or Miniconda) for Python, a distribution and package manager for Python  specifically geared towards data science. This will help download many of the dependencies for the system.

Within Anaconda, create a dedicated environment for development and use with HVF Extraction Script:

```shell
(base) $ conda create --name hvf_env # Replace 'hvf_env' with desired environment name
```

 and switch to that environment:

 ```shell
 (base) $ conda activate hvf_env # or the environment name you chose
 ```

Within your environment, download a few required dependencies with Anaconda, namely PIP (to manage PyPI Package repository) and tesseract:

```shell
(hvf_env) $ conda install pip
...
(hvf_env) $ conda install -c conda-forge tesseract
...
```

Lastly, use PIP to install hvf-extraction-script, to download the package and all other required dependencies:

```shell
(hvf_env) $ pip install hvf-extraction-script
```

Occasionally, installation of hvf-extraction-script has trouble locating some dependencies (specifically tesseract) and fails installation; this may be due to some internal links not refreshing. Try restarting your terminal program and trying again.

## Usage

### Overview

HVF data can be stored in a variety of formats that can be imported into the hvf_extraction_script platform. The platform can import data from 1) HVF report images (PNG, JPG, etc - any file format that openCV can read), 2) HVF DICOM files, and 3) serialized JSON files (produced by the script platform). See below for examples on how to import data from these different sources.

Once imported, data is managed primarily through the Hvf_Object class, which contains the report metadata (name/ID, test date, field size and strategy, etc), and the 5 data plots (raw sensitivity, total deviation value/percentile plots, and pattern deviation value/percentile plots). Plot data is stored as Hvf_Plot_Array objects (internally as 10x10 Numpy arrays), and individual plot data elements are stored as either Hvf_Value or Hvf_Perc_Icon objects. See below for the basic structure of Hvf_Object (and helper classes).

Data modules (which are Hvf_Object, Hvf_Plot_Array, Hvf_Value, Hvf_Perc_Icon) are contained in the subpackage hvf_data. hvf_extraction_script also includes two other subpackages, hvf_manager and utilities, that contain modules to assist in data processing.

Subpackage hvf_manager contains functions to 'manage' or process HVF data. This includes a module for running unit tests for image extraction (hvf_test) and a module for exporting Hvf_Objects to human-readable spreadsheet for further processing (hvf_export). There is also a module for calculating HVF metrics (hvf_metric_calculator), but this module is still under development.

Subpackage utilities contains general purpose utility modules not specific to HVF data. This includes a module for file I/O (file_utils), image processing (image_utils), OCR functions (ocr_utils - essentially a wrapper for TesserOCR), and regex functions (regex_utils).

### Importing and exporting data

Importing/extracting data from an image:

```shell
from hvf_extraction_script.hvf_data.hvf_object import Hvf_Object
from hvf_extraction_script.utilities.file_utils import File_Utils

hvf_img_path = "path/to/hvf/image/file/to/read";
hvf_img = File_Utils.read_image_from_file(hvf_img_path);
hvf_obj = Hvf_Object.get_hvf_object_from_image(hvf_img);
```

Importing data from a DICOM file:

```shell
from hvf_extraction_script.hvf_data.hvf_object import Hvf_Object
from hvf_extraction_script.utilities.file_utils import File_Utils

hvf_dicom_path = "path/to/hvf/dicom/file/to/read";
hvf_dicom = File_Utils.read_dicom_from_file(hvf_dicom_path);
hvf_obj = Hvf_Object.get_hvf_object_from_dicom(hvf_dicom);
```

Saving as a text file:
```shell
serialized_string = hvf_obj.serialize_to_json();
txt_file_path = “path/to/target/file/to/write”;
File_Utils.write_string_to_file(serialized_string, target_file_path)
```

Reinstantiating Hvf_Object from text file
```shell
hvf_txt = File_Utils.read_text_from_file(txt_file_path);
hvf_obj = Hvf_Object.get_hvf_object_from_text(hvf_txt);
```

Export to spreadsheet (tab-separated values):
```shell
# Takes in a dictionary of filename_string -> hvf_obj
from hvf_extraction_script.hvf_manager.hvf_export import Hvf_Export;

dict_of_hvf_objs = {“file1.PNG”: hvf_obj1, “file2.PNG”: hvf_obj2, “file3.PNG”: hvf_obj3 };
spreadsheet_string = Hvf_Export.export_hvf_list_to_spreadsheet(dict_of_hvf_objs)
File_Utils.write_string_to_file(return_string, "output_spreadsheet.tsv")
# Saves data in a spreadsheet, with first column as filename
```

Import Hvf_Objects from outputted spreadsheet (tab-separated values):
```shell
tsv_file_string = File_Utils.read_text_from_file("output_spreadsheet.tsv");
dict_of_hvf_objs = Hvf_Export.import_hvf_list_from_spreadsheet(tsv_file_string);
# Returns dictionary of filename_string -> hvf_obj
```

### Structure of Hvf_Object and helper classes

Hvf_Object contains data from the source HVF study within instance variables. Metadata (including name, ID, field size, reliability indices, etc) are stored within a instance variable dictionary; data is accessible using keys stored within Hvf_Object as constants:

- KEYLABEL_LAYOUT # Internal data corresponding to layout of source HVF image
- KEYLABEL_NAME
- KEYLABEL_DOB
- KEYLABEL_ID
- KEYLABEL_TEST_DATE
- KEYLABEL_LATERALITY
- KEYLABEL_FOVEA
- KEYLABEL_FIXATION_LOSS
- KEYLABEL_FALSE_POS
- KEYLABEL_FALSE_NEG
- KEYLABEL_TEST_DURATION
- KEYLABEL_FIELD_SIZE
- KEYLABEL_STRATEGY
- KEYLABEL_PUPIL_DIAMETER
- KEYLABEL_RX
- KEYLABEL_MD
- KEYLABEL_PSD
- KEYLABEL_VF

Metadata can be accessed from the object as such:

```shell
# As example, accessing name:
name = hvf_obj.metadata[Hvf_Object.KEYLABEL_NAME];
```

Additionly, there are 5 plots in every HVF object, represented by Hvf_Plot_Array objects. These can be accessed by:

```shell
# Raw sensitivity array:
hvf_obj.raw_value_array

# Total deviation value array:
hvf_obj.abs_dev_value_array

# Pattern deviation value array:
hvf_obj.pat_dev_value_array

# Total deviation percentile array:
hvf_obj.abs_dev_percentile_array

# Pattern deviation percentile array:
hvf_obj.pat_dev_percentile_array
```

The main data in the Hvf_Plot_Array object are:

```shell
array_obj.plot_type
# Possible values are Hvf_Plot_Array.PLOT_RAW, Hvf_Plot_Array.PLOT_TOTAL_DEV or Hvf_Plot_Array.PLOT_PATTERN_DEV

array_obj.icon_type
# Possible values are Hvf_Plot_Array.PLOT_VALUE or, Hvf_Plot_Array.PLOT_PERC

array_obj.plot_array
# 10x10 Numpy array containing either Hvf_Value or Hvf_Perc_Icon (depending on icon_type) representing the value of the plot in that position  
```

Hvf_Value is essentially a wrapper class for a numerical value in a value plot (only relevant datum in this object is Hvf_Value.value, the number to wrap). There are some special non-numerical values that this object can take in specific circumstances, including:

- Hvf_Value.VALUE_NO_VALUE (ie, a blank value - for areas in the plot that are empty) - ' '
- Hvf_Value.VALUE_FAILURE (ie, the program was unable to determine was the value was - in other words, an program error) '?'
- Hvf_Value.VALUE_BELOW_THRESHOLD (the value '<0') - '<0 '

Values from Hvf_Value can be queried by calling the method get_value() (ie, hvf_value_obj.get_value()) to get the raw value wrapped, or get_display_string(), which will convert the above cases to a display character/string version for easy reading.

Hvf_Perc_Icon is a similar wrapper class for a percentile icon in a percentile plot (again, only relevant datum in this object is Hvf_Perc_Icon.perc_enum, an enum value corresponding to the icon it represents). The possible values are:

- Hvf_Perc_Icon.PERC_NO_VALUE (ie, a blank value - for areas in the plot that are empty) - ' '
- Hvf_Perc_Icon.PERC_NORMAL (a 'normal' sensitivity - single dot icon) - '.'
- Hvf_Perc_Icon.PERC_5_PERCENTILE (lower than 5th percentile) - '5'
- Hvf_Perc_Icon.PERC_2_PERCENTILE (lower than 2nd percentile) - '2'
- Hvf_Perc_Icon.PERC_1_PERCENTILE (lower than 1st percentile) - '1'
- Hvf_Perc_Icon.PERC_HALF_PERCENTILE (lower than 0.5th percentile - full black box) - 'x'
- Hvf_Perc_Icon.PERC_FAILURE (the program was unable to determine was the value was - in other words, an program error) - '?'

Values from Hvf_Perc_Icon can be queried by calling the method get_enum() to get the enum value, or get_display_string(), which will get a character representing the icon.

### Running Unit Tests

Single Image Testing:

Running a single image test performs an extraction of an image report, shows its extraction data in pretty-print, and tests serialization/deserialization procedures

```shell
from hvf_extraction_script.hvf_manager.hvf_test import Hvf_Test
from hvf_extraction_script.utilities.file_utils import File_Utils

image_path = “path/to/image/file.PNG”;
hvf_image = File_Utils.read_image_from_file(image_path);
Hvf_Test.test_single_image(hvf_image);
…
```

Unit Testing:

This package comes with the ability to run unit tests, but with no pre-loaded unit tests to run. Unit testing code is under Hvf_Test, with some example code in hvf_object_testers.py (uploaded in GitHub source code). In general, unit testing can perform testing comparison between:
- Image extraction vs serialized reference
- Image extraction vs DICOM file reference
- Serialized text file vs DICOM file reference
- Serialized text file vs serialized reference

The image file and reference test files are stored under hvf_test_cases with corresponding names.

Adding unit tests:

```shell
unit_test_name = “unit_test_name”
test_type = Hvf_Test.UNIT_TEST_IMAGE_VS_DICOM;
ref_data_path = "path/to/dicom/file.dcm"
test_data_path = “path/to/image/file.PNG”;
Hvf_Test.add_unit_test(test_name, test_type, ref_data_path, test_data_path);

```

Running unit tests:
```shell
Hvf_Test.test_unit_tests(unit_test_nam, test_type)
...
[SYSTEM] ================================================================================
[SYSTEM] Starting test: v2_26
[SYSTEM] Test v2_26: FAILED ==============================
[SYSTEM] - Metadata MISMATCH COUNT: 1
[SYSTEM] --> Key: pupil_diameter - expected: 4.1, actual: 4.7
[SYSTEM] - Raw Value Plot: FULL MATCH
[SYSTEM] - Total Deviation Value Plot: FULL MATCH
[SYSTEM] - Pattern Deviation Value Plot: FULL MATCH
[SYSTEM] - Total Deviation Percentile Plot: FULL MATCH
[SYSTEM] - Pattern Deviation Percentile Plot: FULL MATCH
[SYSTEM] END Test v2_26 FAILURE REPORT =====================
[SYSTEM] ================================================================================
[SYSTEM] Starting test: v2_27
[SYSTEM] Test v2_27: PASSED
[SYSTEM] ================================================================================
[SYSTEM] Starting test: v2_28
[SYSTEM] Test v2_28: PASSED
[SYSTEM] ================================================================================
...
[SYSTEM] ================================================================================
[SYSTEM] UNIT TEST AGGREGATE METRICS:
[SYSTEM] Total number of tests: 30
[SYSTEM] Average extraction time per report: 4741ms
[SYSTEM]
[SYSTEM] Total number of metadata fields: 510
[SYSTEM] Total number of metadata field errors: 7
[SYSTEM] Metadata field error rate: 0.014
[SYSTEM]
[SYSTEM] Total number of value data points: 3817
[SYSTEM] Total number of value data point errors: 2
[SYSTEM] Value data point error rate: 0.001
[SYSTEM]
[SYSTEM] Total number of percentile data points: 3309
[SYSTEM] Total number of percentile data point errors: 0
[SYSTEM] Percentile data point error rate: 0.0
```

## Authors
- Murtaza Saifee, MD - Ophthalmology resident, UCSF. Email: saifeeapps@gmail.com

## Validation
In progress

## License
GPL License

## Using/Contributing
This project was developed in the spirit of facilitating vision research. To that end, we encourage all to download, use, critique and improve upon the project. Fork requests are encouraged. Research collaboration requests are also welcomed.

## Acknowledgements
- PyImageSearch for excellent tutorials on image processing
