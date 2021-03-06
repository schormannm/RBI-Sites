#!/usr/bin/python
# -*- coding: utf-8 -*-

__author__ = 'mark schormann'

import datetime
import lxml.etree as ET
import fnmatch
import os
import os.path
from collections import OrderedDict

from openpyxl import Workbook
from openpyxl import load_workbook

import sys

import argparse

import xmltodict, json

from dbhelper import DBHelper

# Examples of directories where files might be.
# dir ="/home/mark/Briefcase/Storage/ODK Briefcase Storage/forms"
# dir ="C:\\RBI-Data\\Briefcase\\ODK Briefcase Storage\\forms"

spacer = "\n============================================================++++=========================\n"

S3_URL = "http://rbi-tech-storage.s3.amazonaws.com/forms/"

DB = DBHelper()

def parse_element(element):
    dict_data = dict()
    if element.nodeType == element.TEXT_NODE:
        dict_data['data'] = element.data
    if element.nodeType not in [element.TEXT_NODE, element.DOCUMENT_NODE,
                                element.DOCUMENT_TYPE_NODE]:
        for item in element.attributes.items():
            dict_data[item[0]] = item[1]
    if element.nodeType not in [element.TEXT_NODE, element.DOCUMENT_TYPE_NODE]:
        for child in element.childNodes:
            child_name, child_dict = parse_element(child)
            if child_name in dict_data:
                try:
                    dict_data[child_name].append(child_dict)
                except AttributeError:
                    dict_data[child_name] = [dict_data[child_name], child_dict]
            else:
                dict_data[child_name] = child_dict
    return element.nodeName, dict_data

# ...
#
# This function takes an ODK Storage directory a returns a list of paths for files that are XML files in that directory.
# It also shows which of the sub-directories are valid data containing sub-directories
#
# Valid questions - what about the .mog files from the transmogrifier step?
# ...
def get_files(dir, file_pattern_to_match):
    file_matches = []
    count = 0

    for root, dirnames, filenames in os.walk(dir):
        # print root
        # print dirnames
        # print filenames
        for filename in fnmatch.filter(filenames, file_pattern_to_match):
            file_matches.append(os.path.join(root, filename))
            uuid_paths.append(root)
            if "instances" not in root and "forms" in root:  # the two are necessary to have a valid root node
                print "Root directory : " + root
            count += 1

    print "Examined ", count, " files"

    return file_matches

def write_json_file(input_file):
    f2 = open('submission2.json', 'w')
    o = xmltodict.parse(open(input_file, 'r').read())
    f2.write(json.dumps((o), sort_keys=True, indent=4))
    f2.close()

def fix_header(input_file):
    line = open(input_file,'r').read()
    pos = line.find(' ', 0, 40)  # find first space - we want to change what is before it
    new_line = "<PSEIA" + line[pos:]  # Set first part of string to this value
    pos = new_line.find('</PSEIA', len(new_line) - 40)  # find occurrence at end of file
    new_line = new_line[0:pos] + '</PSEIA>'  # replace with this
    # print new_line
    return new_line


def get_site_data(file_name):
    fixed_xml = fix_header(file_name)  # required to be able to strip off the outer layer
    dict = xmltodict.parse(fixed_xml)  # dict is a dictionary
    site_data = OrderedDict(dict.get('PSEIA'))  # needed to strip off outside layer of XML  - not needed

    updated_site_data = insert_meta_data(site_data, file_name)  # important to initialise the meta data here
    return updated_site_data


def insert_meta_data(site_data, file_name):
    mog_path = uuid_paths[matches.index(file_name)]
    root_path = mog_path[:-3]
    raw_file_name = root_path + "submission.xml"
    # print "Root path : " + root_path
    archived_status = False
    if "Archive" in root_path:
        archived_status = True
    tag = "/forms/"
    pos = root_path.find(tag)
    image_URL = S3_URL + root_path[pos + len(tag):]

    site_data["meta"] = {}  # create the dictionary to contain the meta data
    site_data["meta"]["insert_time"] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    site_data["meta"]["file_path"] = root_path
    site_data["meta"]["file_name"] = raw_file_name
    site_data["meta"]["mog_file_name"] = file_name
    site_data["meta"]["file_archived"] = archived_status
    site_data["meta"]["processed"] = False      # has the file been processed at all
    site_data["meta"]["edited"] = False         # has the file been edited?
    site_data["meta"]["last_edited"] = ""       # when was the file last edited
    site_data["meta"]["reprocessed"] = False    # been reprocessed after edit?  Set FALSE if edited
    site_data["meta"]["injected"] = False       # been injected? Set FALSE if edited
    site_data["meta"]["reported"] = False       # report been generated?  Set False if edited
    site_data["meta"]["image_base_url"] = image_URL

    return site_data


def save_to_file(filename, new_line):  # really not much reason to write to file from here
    try:
        f1 = open(filename, 'w')
        try:
            f1.write(new_line)
        except:
            print "File " + filename + " cannot be written to"
        finally:
            f1.close()
    except:
        print "File " + filename + " cannot be opened"
        return False
    return True


#=============================================================================================================
#
# The filldb program traverses the directory tree of ODK Storage and stores the content of each site within
# the mog subdirecory of each of the UUID directories in the directory structure
# into a MongoDB database
#
start_time = datetime.datetime.now()

parser = argparse.ArgumentParser(
    description="takes an Aggregate XML file that has been mogrified and sticks it in the database")
parser.add_argument("input_filename", help="the name of the input XML file without path")
parser.add_argument("dir", help="the base path under which all the XML files reside in their "
                                "respective sub-directories")

try:
    args = parser.parse_args()
except argparse.ArgumentError, exc:
    print exc.message, '\n', exc.argument

input_filename = args.input_filename
dir = args.dir

print "\nDatabase Filler starting up ...."
records_at_start = DB.number_of_records()

if not os.path.exists(dir):
    print "Horror - input directory " + dir, " does NOT exist! That's BAD! Check your commandline parameters."
    exit()
else:
    print "Great - input directory -> " + dir + " - EXISTS. All good."

    uuid_paths = []
    sites = []
    file_pattern_to_match = "*.mog"

    matches = get_files(dir, file_pattern_to_match)
    total_file_count = len(matches)

    print "Found ", total_file_count, " ", file_pattern_to_match, " files to search"

    file_count = 0
    found_count = 0
    new_count = 0

    for file_name in matches:               # matches is a list of directories that have xml files in them
        file_count += 1
        dir, infilename = os.path.split( file_name)     # actually dealing with full paths here

        if "uuid" in dir:  # there are some directories that do have .mog or xml files in but are not relevant
            # print "Input " + file_name
            site_data = get_site_data(file_name)  # this is a dictionary containing a sites data
            site_id = site_data["@instanceID"]  # site data comes in as a dictionary, so we can search for records based on it

            if DB.check_existing_site(site_data, site_id):  # returns True if site already exists
                print "Found match in db - not adding -> but need to check"  # site exists in database, check integrity
                file_path_db = DB.get_meta_file_path(site_id)
                print "DB file path : " + file_path_db
                print "Current file path : " + file_name
                found_count += 1
            else:
                print "Would have added the site"
                new_count += 1
                # if DB.add_site(site_data, site_id):
                #     print "Completed processing of file # " + str(file_count) + " out of " + str(total_file_count)

print spacer

records_at_end = DB.number_of_records()
delta_records = records_at_end - records_at_start
end_time = datetime.datetime.now()
delta_time = end_time - start_time

print "Elapsed time : " + str(delta_time) + " seconds"
print "From database"
print "Started with : " + str(records_at_start)
print "Ended with : " + str(records_at_end)
print "Number of records added : " + str(delta_records)
print "From program"
print "Number of records found as existing : " + str(found_count)
print "Number of records not found : " + str(new_count)
