from collections import defaultdict
from difflib import SequenceMatcher
import math
import operator
import re
from typing import Any, Iterable


def clean_value(value: str) -> Any:
    """ Determine if the value needs its type changed because for example,
    Happy returns strings for this numbers. Additionally, return None if an
    empty string is provided.

    Args:
        value (str): Value stored for a field

    Returns:
        Any: Value that has correct type if it passed tests or cleaned
        value
    """

    # check if value is an empty string + check if value is not 0
    # otherwise it returns None
    if not value and value != 0:
        return None

    try:
        float(value)
    except ValueError:
        # some picard tool can return "?", why i do not know but i wanna
        # find those people and have a talk with them
        # other tools have NA, so handle those cases
        if value == "?" or value == "NA":
            return None

        # Probably str
        return value

    # nan doesn't trigger the exception, so handle them separately
    if math.isnan(float(value)):
        return None

    # it can float, check if it's an int or float
    if '.' in str(value):
        return float(value)
    else:
        return int(value)


def clean_sample_naming(data):
    """ Clean the sample names.
    Issue encountered with old RD runs for NA12878:
    NA12878-NA12878-1-TWE-F-EGG4_S31_L001_R1 for FastQC NA12878_INDEL_ALL
    for Happy.
    This means that 2 instances of NA12878 are created and the data for the
    sample is split between the 2 instances.
    This function tries to fix that and merge the data.

    Args:
        data (dict): Full data dict containing the samples, their tools and
        their data

    Returns:
        dict: Full data dict with merged data for overlapping sample names
    """

    data_to_add = {}

    for sample in data:
        pattern = re.compile(sample)
        # find the sample names in which other sample names are present
        matches = [ele for ele in data if re.match(pattern, ele)]

        # one sample name is present in other sample name
        if len(matches) > 1:
            # look for the longest common substring in the matches
            longest_common_substring = find_longest_common_substring(matches)
            data_to_add.setdefault(
                longest_common_substring.rstrip("-").rstrip("_"), []
            ).extend(matches)

        elif len(matches) == 1:
            # sample name matched itself, leaving this if for visibility
            continue

        else:
            raise Exception("Well mate time to go to sleep")

    filter_longer_sample_names = []

    # loop through the sample names that matched other sample names
    for sample in data_to_add:
        # This is to take into account cases where more than 2 sample names
        # overlap i.e.
        # string1, string1_string1, string1-string1 -> have string1 as the
        # key for the data for string1_string1 and string1-string1
        overlapping_sample_names = [
            ele for ele in data_to_add
            if sample in ele and len(sample) < len(ele)
        ]

        # if we found bigger sample names, add them to a list for skipping
        # later when merging the data
        if overlapping_sample_names:
            filter_longer_sample_names.extend(overlapping_sample_names)

    for sample_to_add, samples_to_remove in data_to_add.items():
        if sample_to_add in filter_longer_sample_names:
            continue

        merged_data = {}

        # get the data to merge
        for sample_to_remove in samples_to_remove:
            merged_data.update(data[sample_to_remove])
            del data[sample_to_remove]

        data[sample_to_add] = merged_data

    return data

def find_longest_common_substring(strings: Iterable) -> str:
    """ Find the longest common substring in a given iterable

    Args:
        strings (Iterable): Iterable containing strings

    Returns:
        str: Longest common string found in the iterable
    """

    count_substrings = defaultdict(int)

    # look for the longest common substring in the matches
    for i in range(0, len(strings)):
        for j in range(i+1, len(strings)):
            match = SequenceMatcher(
                None, strings[i], strings[j]
            ).find_longest_match(
                0, len(strings[i]), 0, len(strings[j])
            )
            matching_substring = strings[i][match.a:match.a + match.size]
            count_substrings[matching_substring] += 1

    max_occurring_substring = max(
        count_substrings.items(), key=operator.itemgetter(1)
    )[0]

    return max_occurring_substring