#!/usr/bin/python
# -*- coding: utf-8 -*-

__author__ = 'mark schormann'

import datetime
import lxml.etree as ET
import fnmatch
import os
import os.path
import collections
from collections import OrderedDict

from openpyxl import Workbook
from openpyxl import load_workbook

import sys

import argparse

import xmltodict, json

namespace_string = "{http://opendatakit.org/submissions}"

spacer = "\n============================================================++++=========================\n"
thin_spacer = "-----------------------------------------------------------------------------------------\n"

tags_to_match = {"instanceID": 1,
                 "site_name": 2,
                 "site_number": 3,
                 "inspector_name": 4,
                 "region": 5,
                 "date_of_inspection": 7,
                 "tower_owner": 9,
                 "tower_type": 10,
                 "tower_total_height": 13
                 }

file_pattern_to_match = "*.mog"


# ...
#
# This function does the modification in place of individual tag values to fix them so that
# they don't need to be altered later.
#
# The order of the operations matters as some interdependencies exist
# ...
def scan(doc):
    site_data = {}  # empty dictionary for our values to go in
    for el in doc.xpath("//*"):  # process all elements
        text = el.text  # get the text part of the element
        tag = el.tag  # get the tag part of the element

        if text:

            clean_tag = tag.partition("}")  # partition function returns a tuple
            tag_core = clean_tag[2]

            if tag_core in tags_to_match:
                # print tag_core + " = " + text
                site_data[tag_core] = text

    return site_data


# print thin_spacer
parser = argparse.ArgumentParser(description="takes an Aggregate XML file and produces summary of file")
parser.add_argument("input_filename", help="the name of the input XML file with full path")

try:
    args = parser.parse_args()
except argparse.ArgumentError, exc:
    print exc.message, '\n', exc.argument

file_name = args.input_filename

# print "\nSummary generator starting up ...."

print "In: " + file_name

# input
doc = ET.parse(file_name)

# get data from doc
site_data = scan(doc)

for tag in tags_to_match:
    print tag + " : " + site_data[tag]
