###############################################################################
# regex_utils.py
#
# Description:
# 	Class definition for regex utility functions
#
###############################################################################

# Import necessary packages
# Import regular expression packages
import os
import re
from glob import glob

import regex
from fuzzysearch import find_near_matches
from fuzzywuzzy import fuzz, process


class Regex_Utils:
    ###############################################################################
    # CONSTANTS AND STATIC VARIABLES ##############################################
    ###############################################################################

    REGEX_FAILURE = "Extraction Failure"

    ###############################################################################
    # REGEX METHODS ###############################################################
    ###############################################################################

    ###############################################################################
    # Given a label and a list of strings to search within, fuzzy matches the label into
    # the best-matched string and returns the field following the label.
    # Example:
    #    Label = "Name: "
    #    String = ["Na'me: Smith, John", "ID:55555555", "Fovea: 35?B"]
    #    Returns: "Smith, John"
    @staticmethod
    def fuzzy_regex(label, string_list):

        ret = ""

        # Only remove the best-matched string if we have a good score. If the score is poor,
        # possible that its a wrong match and deleting it will cause that field to have
        # a wrong match
        threshold_to_remove = 85

        filtered_string_list = list(filter(lambda x: len(x) >= len(label), string_list))

        if len(filtered_string_list) == 0:

            ret = Regex_Utils.REGEX_FAILURE

        else:

            # First, search and extract the highest match:
            string_match = process.extractOne(label, filtered_string_list, scorer=fuzz.partial_ratio)
            string = string_match[0]
            score = string_match[1]

            # If its a sufficiently high match, then remove it from the list to help next searches
            if score >= threshold_to_remove:
                string_list.remove(string)

            # Fuzzysearch for best match of label within the string:
            match = find_near_matches(label, string, max_l_dist=2)

            # Need to sort and pull out best match:

            if len(match) == 0:
                ret = Regex_Utils.REGEX_FAILURE

            else:

                best_match = sorted(match, key=lambda i: i.dist)[0]

                # Convert the best match into actual string slice
                best_match_string = string[best_match.start : best_match.end]

                # Construct regex based on this slice
                regex = best_match_string + r"\s*(.*)"

                try:
                    # Perform the regex search to find the text of interest
                    output = re.search(regex, string)

                    ret = output.group(1)

                except Exception:
                    print(label + " Failed searches")
                    ret = Regex_Utils.REGEX_FAILURE

        return ret, string_list

    @staticmethod
    def strict_regex(label, string_list):

        ret = ""

        # Only remove the best-matched string if we have a good score. If the score is poor,
        # possible that its a wrong match and deleting it will cause that field to have
        # a wrong match
        threshold_to_remove = 85

        filtered_string_list = list(filter(lambda x: len(x) >= len(label), string_list))

        if len(filtered_string_list) == 0:

            ret = Regex_Utils.REGEX_FAILURE

        else:

            # First, search and extract the highest match:
            string_match = process.extractOne(label, filtered_string_list, scorer=fuzz.partial_ratio)
            string = string_match[0]
            score = string_match[1]

            # If its a sufficiently high match, then remove it from the list to help next searches
            if score >= threshold_to_remove:
                string_list.remove(string)

            # Fuzzysearch for best match of label within the string:
            match = find_near_matches(label, string, max_l_dist=1)

            # Need to sort and pull out best match:

            if len(match) == 0:
                ret = Regex_Utils.REGEX_FAILURE

            else:

                best_match = sorted(match, key=lambda i: i.dist)[0]

                # Convert the best match into actual string slice
                best_match_string = string[best_match.start : best_match.end]

                # Construct regex based on this slice
                regex = best_match_string + r"\s*(.*)"

                try:
                    # Perform the regex search to find the text of interest
                    output = re.search(regex, string)

                    ret = output.group(1)

                except Exception:
                    print(label + " Failed searches")
                    ret = Regex_Utils.REGEX_FAILURE

        return ret, string_list

    ###############################################################################
    # Given a label, a regular expression, and a list of strings to search within, fuzzy
    # matches the label into the best-matched string within the list, then applies the
    # regex onto that string to extract the string of interest
    # Example:
    #    Label = Central Threshold"
    #    regex_str = "Central (.*) Threshold{e<=2}"
    #    String = ["Na'me: Smith, John", "ID:55555555", "Fovea: 35?B", Centra'l 24-2 Threshold]
    #    Returns: "24-2"

    @staticmethod
    def fuzzy_regex_middle_field(label, regex_str, string_list):

        ret = ""

        filtered_string_list = list(filter(lambda x: len(x) >= len(label), string_list))

        # Only remove the best-matched string if we have a good score. If the score is poor,
        # possible that its a wrong match and deleting it will cause that field to have
        # a wrong match
        threshold_to_remove = 85

        if len(filtered_string_list) == 0:
            ret = Regex_Utils.REGEX_FAILURE
        else:

            # First, search and extract the highest match:
            string_match = process.extractOne(label, filtered_string_list, scorer=fuzz.partial_token_sort_ratio)

            if string_match is None:
                ret = Regex_Utils.REGEX_FAILURE

            else:
                string = string_match[0]
                score = string_match[1]

                # If its a sufficiently high match, then remove it from the list to help next searches
                if score >= threshold_to_remove:
                    string_list.remove(string)

                # Perform the regex search to find the text of interest
                output = regex.search(regex_str, string)

                try:
                    ret = output.group(1)

                except Exception:
                    ret = Regex_Utils.REGEX_FAILURE

        return ret, string_list

    ###############################################################################
    # Removes any spaces from the string. Pass through if extraction failure.
    def remove_spaces(string):

        if string == Regex_Utils.REGEX_FAILURE:
            return string

        else:
            return string.replace(" ", "")

    ###############################################################################
    # Cleans up erroneous punctuation. Pass through if extraction failure.
    def clean_punctuation_to_period(string):
        if string == Regex_Utils.REGEX_FAILURE:
            return string

        else:
            string = string.replace(",", ".")
            string = string.replace(";", ".")
            string = ".".join(list(filter(None, string.split("."))))

            return string

    ###############################################################################
    # Removes non-numeric characters from the string. Keeps number characters, '.' and '-'
    def remove_non_numeric(string, safe_char_list):
        if string == Regex_Utils.REGEX_FAILURE:
            return string

        else:

            regex_str = "^0-9"

            for char in safe_char_list:
                regex_str = regex_str + "^\\" + char

            string = re.sub(f"[{regex_str}]", "", string)

            return string

    ###############################################################################
    # Adds a decimal point if none is detect. Assumes that number should have 2 spaces
    # after decimal point
    def add_decimal_if_absent(string):
        if string == Regex_Utils.REGEX_FAILURE:
            return string
        elif not (re.search(r"(\.)", string) and len(string) > 2):

            i = len(string) - 2

            string = string[:i] + "." + string[i:]

        return string

    ###############################################################################
    # Clean minus sign. Condense any similar-looking prefixes into a single minus sign
    @staticmethod
    def clean_minus_sign(string):
        if string == Regex_Utils.REGEX_FAILURE:
            return string
        else:
            string = re.sub(r"(\=)+", "-", string)
            string = re.sub(r"^(\-)+", "-", string)

        return string

    ###############################################################################
    # Clear out non ASCII unicode characters
    @staticmethod
    def clean_nonascii(string: str) -> str:
        if string == Regex_Utils.REGEX_FAILURE:
            return string
        else:
            string = string.encode("ascii", "ignore").decode("unicode_escape")

        return string

    @staticmethod
    def temp_out(debug_dir: str = ".", string: str = "debug_pass_") -> str:
        max_val = 0
        string2 = os.path.join(debug_dir, string)
        gg = [re.search(r"_(\d+)\.", x) for x in glob(f"{string2}*.*")]
        if gg:
            max_val = max(map(int, [x.group(1) for x in gg]))  # type: ignore
        return f"{string2}{max_val+1}"
