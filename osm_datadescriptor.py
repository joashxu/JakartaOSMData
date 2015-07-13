#!/usr/bin/env python
# -*- coding: utf-8 -*-

import xml.etree.cElementTree as ET
import re


class OSMDataDescriptor(object):
    '''
    OSMDataDescriptor.
    Simple class to summarize OSM data.
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
