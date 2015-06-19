#!/usr/bin/env python
# -*- coding: utf-8 -*-

import xml.etree.cElementTree as ET


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
        for event, elem in ET.iterparse(self.filename, events=("start",)):
            for tag in elem.iter("tag"):
                tag_keys[tag.attrib['k']] = tag_keys.get(tag.attrib['k'], 0) + 1

        return sorted(tag_keys.items(), key=lambda x: x[0])
