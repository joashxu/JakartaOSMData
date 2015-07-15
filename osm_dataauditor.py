#!/usr/bin/env python
# -*- coding: utf-8 -*-

import xml.etree.cElementTree as ET
import re
import json
import itertools
from difflib import SequenceMatcher


class OSMDataAuditor(object):
    '''
    This class summarize and audit OSM Data.
    '''

    def __init__(self, filename):
        self.filename = filename

    def count_element(self):
        '''Return element and its total.'''
        tags = {}
        context = ET.iterparse(self.filename)
        for event, element in iter(context):
            tags[element.tag] = tags.get(element.tag, 0) + 1

        return tags

    def get_tag_keys(self):
        '''Return list of sorted tag of key attribute and its total.'''
        tag_keys = {}
        for event, elem in ET.iterparse(self.filename, events=('start',)):
            for tag in elem.iter("tag"):
                tag_keys[tag.attrib['k']] = tag_keys.get(tag.attrib['k'], 0) + 1

        return sorted(tag_keys.items(), key=lambda x: x[0])

    def audit_abbreviated_street_prefixes(self):
        '''Check the address prefixes for street.

        Faulty street address will startswith:
            jln, jln., jl, jl.
        '''

        street_regx = re.compile(r'^(jln?\.?)\s?(.*)', re.IGNORECASE)
        faulty_street_prefixes = []

        for event, element in ET.iterparse(self.filename, events=('start',)):
            # Only pay attention to 'way' tag
            if not element.tag == 'way':
                continue

            for el in element.iter('tag'):
                # We audit both addr:street and addr:full, since
                # a lot of address is in the addr:full tag.
                if el.attrib['k'] == 'addr:street' or el.attrib['k'] == 'addr:full':
                    if street_regx.match(el.attrib['v']):
                        faulty_street_prefixes.append(el.attrib['v'])

        return faulty_street_prefixes

    def audit_abbreviated_alley_prefixes(self):
        '''Check the alley prefixes for street.

        Faulty alley address will starts with:
            gg, gg.
        '''

        alley_regx = re.compile(r'^(gg\.?)\s?(.*)', re.IGNORECASE)
        faulty_alley_prefixes = []

        for event, element in ET.iterparse(self.filename, events=('start',)):
            # Only pay attention to 'way' tag
            if not element.tag == 'way':
                continue

            for el in element.iter('tag'):
                # We audit both addr:street and addr:full, since
                # a lot of address is in the addr:full tag.
                if el.attrib['k'] == 'addr:street' or el.attrib['k'] == 'addr:full':
                    if alley_regx.match(el.attrib['v']):
                        faulty_alley_prefixes.append(el.attrib['v'])

        return faulty_alley_prefixes

    def audit_address_similar_names(self, reference_filename='street_name.json'):
        '''Check if the street name match reference from wikipedia.

        The reference is taken from Wikipedia info box.
        Use difflib.SequenceMatcher to check how closely the name in the tag match the reference.
        '''
        # Load wikipedia street name data
        street_names_file = open(reference_filename)
        street_names = json.load(street_names_file)

        # Flatten the street names, ignore the city
        flatten_street_names = [item.lower() for item in itertools.chain(*street_names.values())]

        closely_matched_names = set()
        for event, element in ET.iterparse(self.filename, events=('start',)):
            # Only pay attention to 'way' tag
            if not element.tag == 'way':
                continue

            for el in element.iter('tag'):
                # We only audit addr:street for this.
                if el.attrib['k'] == 'addr:street':
                    street_name = el.attrib['v'].lower()
                    for ref_street_name in flatten_street_names:
                        s = SequenceMatcher(lambda x: x == " ", street_name, ref_street_name)

                        # Check the ratio between the two stings.
                        # 0.6 is considered a close match, I choose 0.65
                        # 1 means the two strings match exactly.
                        # We want ratio that is between the two.
                        if 0.65 <= s.ratio() < 1.0:
                            closely_matched_names.add((ref_street_name, street_name, s.ratio()))

        return closely_matched_names

    def audit_city(self):
        ''' Get unique city name.
        '''
        city_list = set()
        for event, element in ET.iterparse(self.filename, events=('start',)):
            # Only pay attention to 'way' tag
            if not element.tag == 'way':
                continue

            for el in element.iter('tag'):
                for el in element.iter('tag'):
                    if el.attrib['k'] == 'addr:city':
                        city_list.add(el.attrib['v'].lower())

        return city_list
