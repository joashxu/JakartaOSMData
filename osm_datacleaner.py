#!/usr/bin/env python
# -*- coding: utf-8 -*-

import xml.etree.cElementTree as ET
import re
import json


class OSMDataCleaner(object):
    '''
    OSMDataCleaner.

    This class will clean OSM data and output a JSON.
    '''

    def clean(self, input_path, output_path):
        ''' Clean and store write JSON to file.

        input_path: The file path for OSM data
        output_path: The file path where the JSON data will be stored.
        '''
        shaped_element = self.clean_data(input_path)

        with open(output_path, 'wb') as output:
            json.dump(shaped_element, output)

    def clean_data(self, input_path):
        ''' Clean data step-by-step.

        We first shape the element into json, and clean it in JSON format, step-by-step.
        '''
        data = []
        for event, elem in ET.iterparse(input_path, events=("start",)):
            document = self.shape_element(elem)
            if document:
                data.append(document)

        # Clean address
        data = self.cleanup_address_street(data)

        # Clean alley
        data = self.cleanup_address_alley(data)

        # Clean up similar names
        data = self.cleanup_similar_names(data)

        # Clean up city names
        data = self.cleanup_city(data)

        # Misc. clean up
        data = self.cleanup_misc(data)

        return data

    def is_valid_key(self, key):
        ''' We are going to import the output to MongoDB later,
        so we need to make sure the key is valid.
        '''
        problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')
        if problemchars.search(key):
            return False

        return True

    def shape_element(self, element):
        '''
        Turn element into valid JSON object.
        '''
        node = {}

        if not element.tag == "node" and not element.tag == "way":
            # Return empty dictionary if the tag is neither 'node' or 'way'
            return node

        # Get ID
        node['id'] = element.attrib['id']

        # Get type
        node['type'] = element.tag

        # Visibility
        if element.attrib.get('visible', False):
            node['visible'] = element.attrib['visible']

        # Get Latitude and Longitude
        if element.attrib.get('lat', None) and element.attrib.get('lon', None):
            node['pos'] = [float(element.attrib['lat']),
                           float(element.attrib['lon'])]

        # Store meta information
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

                # Split tag with format <element>:<sub_element>,
                # e.g.: addr:street
                k = k.split(':')

                # Sanity check ignore itemthat has more then
                # one splitter ':'. Not a valid tag:value item.
                if len(k) > 2:
                    continue

                if k[0] == 'addr' and self.is_valid_key(k[1]):
                    # Store the address
                    node['address'][k[1]] = v
                else:
                    k = ':'.join(k)
                    if self.is_valid_key(k):
                        node[k] = v

            # Store node reference
            node_refs = [el.attrib['ref'] for el in element.iter('nd')]
            node['node_refs'] = node_refs

        return node

    def cleanup_address_street(self, data):
        ''' Cleanup street prefix for address.
        '''
        regx = re.compile(r"^(jln?\.?)\s?(.*)", re.IGNORECASE)

        for item in data:
            if not item['type'] == 'way':
                continue

            # Street and full is not mutually exclusive.
            # So we need to process them both.
            if item['address'].get('street', None):
                address = item['address']['street']
                match = regx.match(address)
                if match:
                    address = ' '.join(['Jalan', match.groups()[-1]])
                    item['address']['street'] = address

            if item['address'].get('full', None):
                address = item['address']['full']
                match = regx.match(address)
                if match:
                    address = ' '.join(['Jalan', match.groups()[-1]])
                    item['address']['full'] = address

        return data

    def cleanup_address_alley(self, data):
        ''' Cleanup alley prefix for address.
        '''
        regx = re.compile(r"^(gg\.?)\s?(.*)", re.IGNORECASE)

        for item in data:
            if not item['type'] == 'way':
                continue

            if item['address'].get('street', None):
                address = item['address']['street']
                match = regx.match(address)
                if match:
                    address = ' '.join(['Gang', match.groups()[-1]])
                    item['address']['street'] = address

            if item['address'].get('full', None):
                address = item['address']['full']
                match = regx.match(address)
                if match:
                    address = ' '.join(['Gang', match.groups()[-1]])
                    item['address']['full'] = address

        return data

    def cleanup_similar_names(self, data):
        ''' Clean up the data that contain similiar names.

        The similiar name reference is from Wikipedia.
        The similiar_names_map is manually generated after an audit process,
        in which we use Python difflib.SequenceMatcher to check similarity between
        reference and the entry in data.
        '''

        similiar_names_map = [
            ('Jalan Jenderal Ahmad Yani', 'Jalan Jendral Ahmad Yani'),
            ('Jalan Jenderal Sudirman', 'Jalan Jendral Sudirman'),
            ('Jalan HR Rasuna Said', 'Jalan HR. Rasuna Said'),
            ('Jalan TB Simatupang', 'TB. Simatupang'),
            ('Jalan Patimura', 'Pattimura'),
            ('Jalan HR Rasuna Said', 'Jalan H.R. Rasuna Said'),
            ('Jalan Kapten Tendean', 'Kapten P. Tendean'),
            ('Jalan HR Rasuna Said', 'Jalan H.R.Rasuna Said'),
            ('Jalan Jenderal Gatot Subroto', 'Jalan Jend. Gatot Subroto'),
            ('Jalan MH Thamrin', 'Jalan M. H. Thamrin'),
            ('Jalan Abdul Syafiie', 'KH Abdul Syafi\'ie'),
            ('Jalan Jenderal Sudirman', 'Jalan Jend. Sudirman'),
            ('Jalan Pasar Minggu', 'Jalan Raya Pasar Minggu'),
            ('Jalan Kyai Haji Wahid Hasyim', 'KH Wahid Hasyim'),
            ('Jalan Kapten Tendean', 'Kapten Pierre Tendean'),
            ('Jalan Letnan Jenderal S Parman', 'Letjen S Parman'),
            ('Jalan Kyai Haji Mas Mansyur', 'K.H. Mas Mansyur'),
            ('Jalan Letnan Jenderal MT Haryono', 'Jalan Letjen M. T. Haryono'),
            ('Jalan Jenderal Ahmad Yani', 'Jalan Ahmad Yani'),
            ('Jalan Laksamana Yos Sudarso', 'Jalan Yos Sudarso'),
            ('Jalan Insinyur Haji Juanda', 'Jalan Ir. H. Juanda'),
            ('Jalan Letnan Jenderal S Parman', 'Letjend. Siswondo Parman'),
            ('Jalan Jenderal Gatot Subroto', 'Gatot Soebroto'),
        ]

        for item in data:
            if not item['type'] == 'way':
                continue

            if item['address'].get('street', None):
                for reference, current in similiar_names_map:
                    if item['address']['street'] == current:
                        item['address']['street'] = reference

        return data

    def cleanup_city(self, data):
        '''Clean up entry city names.

        We only do this on city name that is not complete, which is Jakarta.
        '''

        # Open reference file and flatten the item
        street_to_city_map = {}
        with open('street_name.json') as reference:
            street_names = json.load(reference)
            for k, v in street_names.items():
                for item in v:
                    street_to_city_map[item] = k

        for item in data:
            if not item['type'] == 'way':
                continue

            if item['address'].get('street', None) and item['address'].get('city', None):
                is_address_referenced = True if street_to_city_map.get(item['address']['street'], False) else False
                is_city_incomplete = item['address']['city'].lower() == 'jakarta'
                if is_address_referenced and is_city_incomplete:
                    item['address']['city'] = street_to_city_map[item['address']['street']]

        return data

    def cleanup_misc(self, data):
        '''
        Misc. cleanup the fault we find during audit but
        cannot be neatly
        '''
        # Address street that has no prefix, but is known to be street.
        no_prefix_address = {
            'Gunung Sahari 4': 'Jalan Gunung Sahari',
            'Veteran 3': 'Jalan Veteran',
            'Mampang Prapatan 4': 'Jalan Mampang Prapatan'
        }

        # Address street that contain house number.
        with_housenumber = {
            'KH Mas Mansyur no 57': ('Jalan Kyai Haji Mas Mansyur', 57)
        }

        # Faulty city names
        faulty_city_name = {
            'cikini': 'Jakarta Pusat',
            'cilandak': 'Jakarta Selatan',
            'cilandak timur': 'Jakarta Selatan',
            'east tebet': 'Jakarta Selatan',
            'jakarta barat': 'Jakarta Barat',
            'jakarta pusat': 'Jakarta Pusat',
            'jakarta selatan': 'Jakarta Selatan',
            'jakarta timur': 'Jakarta Timur',
            'jakarta utara': 'Jakarta Utara',
            'kemayoran': 'Jakarta Pusat',
            'mampang prapatan': 'Jakarta Selatan',
            'menteng, jakarta pusat': 'Jakarta Pusat',
            'pela mampang, jakarta selatan': 'Jakarta Selatan',
            'tanjung priuk': 'Jakarta Utara'
        }

        for item in data:
            if not item['type'] == 'way':
                continue

            if item['address'].get('street', None):

                # Update data where it has no prefix
                has_no_prefix = no_prefix_address.get(item['address']['street'], False)
                if has_no_prefix:
                    item['address']['street'] = no_prefix_address[item['address']['street']]

                # Update data where it has housenumber in the address
                has_a_housenumber = with_housenumber.get(item['address']['street'], False)
                if has_a_housenumber:
                    street, housenumber = with_housenumber[item['address']['street']]
                    item['address']['street'] = street
                    item['address']['housenumber'] = housenumber

            # Update data that has incomplete or wrong city names
            if item['address'].get('city', None):
                is_city_referenced = faulty_city_name.get(item['address']['city'], False)
                if is_city_referenced:
                    item['address']['city'] = faulty_city_name[item['address']['city']]

        return data
