import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="hvf_extraction_script",
    version="0.0.4",
    author="Murtaza Saifee",
    author_email="saifeeapps@gmail.com",
    description="Python extraction script for HVF report images",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/msaifee786/hvf_extraction_script",
    packages=setuptools.find_packages(),
    package_data={'hvf_extraction_script': ['hvf_data/other_icons/*.PNG', 'hvf_data/perc_icons/*.JPG', 'hvf_data/value_icons/v0/*.PNG', 'hvf_data/value_icons/v1/*.PNG', 'hvf_data/value_icons/v2/*.PNG']},
    install_requires=[
          'tesserOCR',
          'regex',
          'pydicom',
          'pillow',
          'opencv-python',
          'fuzzywuzzy',
          'fuzzysearch',
          'python-levenshtein'
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
