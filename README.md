# HVF Extraction Script

Python module for Humphrey Visual Field (HVF) report data extraction. Extracts data using OCR (tesseract) and image processing techniques (heavily reliant on openCV) to extract data into an object oriented format for further processing.

## Getting Started

### Requirements
- Python 3.6.7 or higher
- TesserOCR
- Regex
- Pillow
- OpenCV 4.2.0
- FuzzyWuzzy
- Fuzzysearch

### Installation

## Usage

Data is managed primarily through the Hvf_Object class, which contains the report metadata (name/ID, test date, field size and strategy, etc), and the 5 data plots (raw sensitivity, total deviation value/percentile plots, and pattern deviation value/percentile plots). Plot data is stored as Hvf_Plot_Array objects (internally as 10x10 Numpy arrays), and individual plot data elements are stored as either Hvf_Value or Hvf_Perc_Icon objects.

### Importing and exporting data

Processing a single image:

```shell
from hvf_extraction_script import Hvf_Object
from hvf_extraction_script import File_Utils

hvf_img = File_Utils.read_image_from_file(hvf_img_path);
hvf_obj = Hvf_Object.get_hvf_object_from_image(hvf_img);
```

Saving as a text file:
```shell
serialized_string = hvf_obj.serialize_to_json();
txt_file_path = “path/to/target/file/to/write”;
File_Utils.write_string_to_file(serialized_string, target_file_path)
```

Reinstantiating from text file
```shell
hvf_txt = File_Utils.read_text_from_file(txt_file_path);
hvf_obj = Hvf_Object.get_hvf_object_from_text(hvf_txt);
```

Export to spreadsheet (tab-separated values):
```shell
# Takes in a dictionary of filename_string -> hvf_obj
from hvf_extraction_script import Hvf_Export;

dict_of_hvf_objs = {“file1.PNG”: hvf_obj1, “file2.PNG”: hvf_obj2, “file3.PNG”: hvf_obj3 };
spreadsheet_string = Hvf_Export.export_hvf_list_to_spreadsheet(dict_of_hvf_objs)
File_Utils.write_string_to_file(return_string, "output_spreadsheet.tsv")
```

Basic data usage:
Structure of hvf_obj and underlying objects


### Running Unit Tests

Single Image Testing:

Running a single image test performs an extraction of an image report, shows its extraction data in pretty-print, and tests serialization/deserialization procedures

```shell
from hvf_extraction_script import Hvf_Test
from hvf_extraction_script import File_Utils

image_path = “path/to/image/file.PNG”;
hvf_image = File_Utils.read_image_from_file(image_path);
Hvf_Test.test_single_image(hvf_image);
…
```

Unit Testing:

The module comes with the ability to run unit tests, but with no pre-loaded unit tests to run. Unit tests are organized into collections under a specified name; they compare data extracted from images against a reference text file . When a unit test image is ‘added’, the module (in its current state) generates the reference file purely from the extraction; the user must then go and manually edit/replace the text file with the corrections to validate the reference file. The image file and reference test files are stored under hvf_test_cases with corresponding names.

Adding unit tests:

```shell
image_path = “path/to/image/file.PNG”;
unit_test_name = “unit_test_name”
Hvf_Test.add_unit_test(image_path, unit_test_name)

# Then, manually correct reference text file under hvf_test_cases
```

Running unit tests:
```shell
Hvf_Test.test_unit_tests(unit_test_name)
...
[SYSTEM] ================================================================================
[SYSTEM] Starting test: v1_30
[SYSTEM] Test v1_30: FAILED ==============================
[SYSTEM] - Metadata: FULL MATCH
[SYSTEM] - Raw Value Plot MISMATCH COUNT: 1
[SYSTEM] --> Element (5, 2) - expected 24, actual 21
[SYSTEM] - Total Deviation Value Plot: FULL MATCH
[SYSTEM] - Pattern Deviation Value Plot: FULL MATCH
[SYSTEM] - Total Deviation Percentile Plot: FULL MATCH
[SYSTEM] - Pattern Deviation Percentile Plot: FULL MATCH
[SYSTEM] END Test v1_30 FAILURE REPORT =====================
[SYSTEM] ================================================================================
[SYSTEM] UNIT TEST AGGREGATE METRICS:
[SYSTEM] Total number of tests: 30
[SYSTEM] Average extraction time per report: 5868ms
[SYSTEM]
[SYSTEM] Total number of metadata fields: 510
[SYSTEM] Total number of metadata field errors: 16
[SYSTEM] Metadata field error rate: 0.031
[SYSTEM]
[SYSTEM] Total number of value data points: 5047
[SYSTEM] Total number of value data point errors: 44
[SYSTEM] Value data point error rate: 0.009
[SYSTEM]
[SYSTEM] Total number of percentile data points: 3453
[SYSTEM] Total number of percentile data point errors: 0
[SYSTEM] Percentile data point error rate: 0.0
```

## Authors
- Murtaza Saifee, MD - Ophthalmology resident, UCSF

## Validation
In progress

## License
GPL License

## Using/Contributing
This project was developed in the spirit of facilitating vision research. To that end, we encourage all to download, use, critique and improve upon the project. Collaboration requests are also welcomed.

## Acknowledgements
- PyImageSearch for excellent tutorials on image processing
