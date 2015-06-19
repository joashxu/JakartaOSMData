#!/usr/bin/env python
# -*- coding: utf-8 -*-

import xml.etree.cElementTree as ET
import re

from pymongo import MongoClient


class OSMDataImporter(object):
    '''
    OSMDataImporter.
    This class import OSM data into MongoDB
    '''

    def __init__(self, db_name='osm_data_import', db_collection_name='jakarta'):
        self.client = MongoClient()
        self.db = self.client[db_name]
        self.collection = self.db[db_collection_name]

    def import_data(self, filename):
        for event, elem in ET.iterparse(filename, events=("start",)):
            document = self.shape_element(elem)
            if document:
                self.collection.insert(document)

    def is_valid_key(self, key):
        problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')
        if problemchars.search(key):
            return False

        return True

    def shape_element(self, element):
        '''
        Turn element into valid MongoDB document.
        '''
        node = {}
        if element.tag == "node" or element.tag == "way":
            node['id'] = element.attrib['id']
            node['type'] = element.tag
            if element.attrib.get('visible', False):
                node['visible'] = element.attrib['visible']
            if element.attrib.get('lat', None) and element.attrib.get('lon', None):
                node['pos'] = [float(element.attrib['lat']),
                               float(element.attrib['lon'])]
            node['created'] = {
                'changeset': element.attrib['changeset'],
                'user': element.attrib['user'],
                'version': element.attrib['version'],
                'uid': element.attrib['uid'],
                'timestamp': element.attrib['timestamp']
            }

            if element.tag == 'way':
                node['address'] = {}
                for el in element.iter('tag'):
                    k, v = el.attrib['k'], el.attrib['v']
                    k = k.split(':')
                    if len(k) > 2:
                        continue

                    if k[0] == 'addr':
                        if self.is_valid_key(k[1]):
                            node['address'][k[1]] = v
                    else:
                        k = ':'.join(k)
                        if self.is_valid_key(k):
                            node[k] = v

                node_refs = [el.attrib['ref'] for el in element.iter('nd')]
                node['node_refs'] = node_refs

            return node
        else:
            return None

    def cleanup_address_street(self):
        regx = re.compile(r"^(jln?\.?)\s?(.*)", re.IGNORECASE)
        entry_with_faulty_address = self.collection.find({
            '$or': [{'address.street': regx}, {'address.full': regx}]
        })

        for item in entry_with_faulty_address:
            # Street and full is not mutually exclusive.
            # So we need to process them both.

            if item['address'].get('street', None):
                address = item['address']['street']
                match = regx.match(address)
                if match:
                    address = ' '.join(['Jalan', match.groups()[-1]])

                self.collection.update({'_id': item['_id']},
                                       {'$set': {'address.street': address}})

            if item['address'].get('full', None):
                address = item['address']['full']
                match = regx.match(address)
                if match:
                    address = ' '.join(['Jalan', match.groups()[-1]])

                self.collection.update({'_id': item['_id']},
                                       {'$set': {'address.full': address}})

    def cleanup_address_alley(self):
        regx = re.compile(r"^(gg\.?)\s?(.*)", re.IGNORECASE)
        entry_with_faulty_address = self.collection.find({
            '$or': [{'address.street': regx}, {'address.full': regx}]
        })

        for item in entry_with_faulty_address:
            if item['address'].get('street', None):
                address = item['address']['street']
                match = regx.match(address)
                if match:
                    address = ' '.join(['Gang', match.groups()[-1]])

                self.collection.update({'_id': item['_id']},
                                       {'$set': {'address.street': address}})

            if item['address'].get('full', None):
                address = item['address']['full']
                match = regx.match(address)
                if match:
                    address = ' '.join(['Gang', match.groups()[-1]])
                self.collection.update({'_id': item['_id']},
                                       {'$set': {'address.full': address}})
