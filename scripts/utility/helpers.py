"""
Различные всопомогательные функции
"""

import csv
import json


def save_to_file(filename, arr):
    with open(filename, 'w') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerows(arr)


def json_save(filename, data):
        with open(filename, 'w') as outfile:
            json.dump(data, outfile, ensure_ascii=False)


def union_jsons(json_files):
    errors = []
    final_data = {}
    for filename in json_files:
        data = json.load(open(filename, 'r'))
        errors += data.pop('errors')
        final_data.update(data)
    final_data['errors'] = errors
    return final_data
