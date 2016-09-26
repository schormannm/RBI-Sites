#

import xmltodict, json
from collections import OrderedDict

import pymongo

from dbhelper import DBHelper

null = None

json_block = {
	"database" : "mkyongDB",
	"table" : "hosting",
	"detail" :
		{
			"records" : 99,
			"index" : "vps_index1",
			"active" : "true"
		}
	}

json_block2 = {
    "PSEIA_Monopole_Inspect_V1-16":
        {
        "@id": "PSEIA_monopole_2015-1.16",
        "@instanceID": "uuid:00add7cf-2716-4eb4-9f91-77119498db9d",
        "@isComplete": "true",
        "@markedAsCompleteDate": "2016-05-25T15:56:22.124Z",
        "@submissionDate": "2016-05-25T15:54:36.426Z",
        "@version": "2016022801",
        "@xmlns": "http://opendatakit.org/submissions",
        "General_terrain":
            {
            "ground_conditions": "Hard_sand",
            "road_conditions_access_ease": "Bakkie",
            "road_conditions_access_type": "Tarred"
            }
    }
}


DB = DBHelper()

# from xml.dom import minidom
# import simplejson as json
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

def write_json_file(input_file):
    f2 = open('submission2.json', 'w')
    o = xmltodict.parse(open(input_file, 'r').read())
    f2.write(json.dumps((o), sort_keys=True, indent=4))
    f2.close()

def fix_header(input_file):
    line = open(input_file,'r').read()
    pos = line.find('id',0,40)
    new_line = "<PSEIA " + line[pos:]
    pos = line.find('</PSEIA',len(line)-40)
    new_line = line[0:pos] + '</PSEIA>'
    print pos

    f1 = open(input_file,'w')
    f1.write(new_line)
    f1.close()

    print new_line


if __name__ == '__main__':

    fix_header('submission.xml')

    dict = xmltodict.parse(open('submission.xml', 'r').read())     # o is a dictionary
    inside = OrderedDict(dict.get('PSEIA'))     # needed to strip off outside layer of XML  - not needed

    try:
        DB.add_site(inside)
    except pymongo.errors.DuplicateKeyError:
        print "Trying to add a duplicate record - ignored"

    client = pymongo.MongoClient()
    db = client["rbi"]

    # print db.sites.create_index("site.instanceID", unique=True) # only needed to run once

    cursor = db.sites.find({"site.tower_type":"Monopole"})

    print  db.sites.count()

    for document in cursor:
        print(document)

    write_json_file('submission.xml')

