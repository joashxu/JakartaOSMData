#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json

from pymongo import MongoClient


class OSMDataImporter(object):
    '''
    OSMDataImporter.

    '''

    def __init__(self, db_name='osm_data_import', db_collection_name='jakarta'):
        self.client = MongoClient()
        self.db = self.client[db_name]
        self.collection = self.db[db_collection_name]

    def import_data(self, filename):
        with open(filename) as data:
            data = json.load(data)
            for item in data:
                self.collection.insert(item)
