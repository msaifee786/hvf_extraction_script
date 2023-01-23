import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="hvf_extraction_script",
    version="0.1.0",
    author="Murtaza Saifee",
    author_email="saifeeapps@gmail.com",
    description="Python extraction script for HVF report images using AWS rekognition as an option as well",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/msaifee786/hvf_extraction_script",
    packages=setuptools.find_packages(),
    package_data={
        "hvf_extraction_script": [
            "hvf_data/other_icons/*.PNG",
            "hvf_data/perc_icons/*.JPG",
            "hvf_data/value_icons/v0/*.PNG",
            "hvf_data/value_icons/v1/*.PNG",
            "hvf_data/value_icons/v2/*.PNG",
        ]
    },
    install_requires=[
        "regex",
        "pydicom",
        "pillow",
        "opencv-python",
        "fuzzywuzzy",
        "fuzzysearch",
        "typed-argument-parser",
        "python-levenshtein",
    ],
    extras_require={
        "tesserOCR": ["tesserOCR"],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
