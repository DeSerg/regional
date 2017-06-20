"""
Модуль приведения найденных с помощью модуля regional_search данных в удобный и
очищенный вид.
"""

import json
import sys
import re


class RegionalJsonPrettifyer:
    def __init__(self, filename, source_type):
        self.data = json.load(open(filename, 'r'))
        self.source_type = source_type
        self.converted_data = {'errors': self.data.pop('errors')}

        self._define_id_generator()
        self._define_field_extractor()


    def prettify(self, filename):
        self._convert_keys()
        self._save(filename)

    # вспомогательная функция, возвращающая функцию, создающую идентификатор
    def _define_id_generator(self):
        if self.source_type == "lj":
            self._id_generator = self._extract_id_for_lj
        # for vk identifier is simply a number
        elif self.source_type == "vk":
            self._id_generator = (lambda i, x: str(i))

    def _define_field_extractor(self):
        self.field_strings = {key: key for key in ['city', 'loc', 'birth', 'year', 'url', 'length']}
        if self.source_type == "lj":
            self.field_strings['author'] = 'author'
        elif self.source_type == "vk":
            self.field_strings['author'] = 'id'

    def _convert_keys(self):
        for i, attr_str in enumerate(self.data, 1):
            id = self._id_generator(i, attr_str)
            if id is not None:
                self.converted_data[id] = self._get_attrs(attr_str)
                self.converted_data[id]['regional_words'] = self.data[attr_str]['regional_words']

    def _get_attrs(self, attr_str):
        hash = {}
        keys = ['city', 'loc', 'birth', 'year', 'author', 'url', 'length']
        for key in keys:
            attr = self._get_attr(self.field_strings[key], attr_str)
            if attr:
                hash[key] = attr[1]
        return hash

    def _get_attr(self, key, attr_str):
        found = re.search('{0}="(.*?)"'.format(key), attr_str)
        if found:
            return (key, found.groups(1)[0])
        else:
            return None

    def _extract_id_for_lj(self, i, attr_str):
        id_match = re.search('id="(.*?)"', attr_str)
        return (id_match.groups(1)[0] if id_match else None)

    def _save(self, filename):
        with open(filename, 'w') as outfile:
            json.dump(self.converted_data, outfile, ensure_ascii=False)


def run(args):
    if len(args) < 3:
        sys.exit("Pass json file, source type ('lj' or 'vk') and save filename")

    filename = args[0]
    source_type = args[1]
    if source_type not in ["lj", "vk"]:
        sys.exit("source type must be 'lj' or 'vk'.")
    save_filename = args[2]

    rjp = RegionalJsonPrettifyer(filename, source_type)
    rjp.prettify(save_filename)
