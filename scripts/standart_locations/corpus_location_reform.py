import os
import sys
import re

locations_map_filename = 'out.txt'
locations_map = {}

loc_replaced = 0
loc_total = 0

def read_locations_map(locations_map_filename):
    with open(locations_map_filename) as loc_f:
        for line in loc_f:
            line_split = line.split('\t\t')
            if len(line_split) != 2:
                print('sad...')
                continue
            origin = line_split[0].strip()
            reform = line_split[1].strip()
            locations_map[origin] = reform


def extract_location(line):
    loc = line.split(',')

    if not loc:
        return ''

    loc = [s.strip() for s in loc]

    line_extr = loc[0]
    for loc_item in loc[1:]:
        line_extr = line_extr + ',' + loc_item
    return line_extr

def reform_location(match):
    global loc_replaced
    global loc_total

    location = match.group(1)
    extr_location = extract_location(location)
    print(extr_location)

    if extr_location in locations_map:
        loc_replaced += 1
        loc_total += 1
        result_loc = locations_map[extr_location]
    else:
        loc_total += 1
        result_loc = extr_location
    return 'Location="' + result_loc + '"'

loc_files = [
    #('body.txt', 90)
    ('/data/kaa/compose/m.lj.compact/groups.txt', 146425),
    ('/data/kaa/compose/m.lj.compact5/groups.txt', 585704),
    ('/data/kaa/compose/m.lj.compactR/groups.txt', 732129)
]

walk_dir = '/data/safe/livejournal.com/pure-texts'
output = 'all_unuqie_locations.txt'


def main(argv):
    if len(argv) != 1:
        print('Usage: script.py locations_map.txt')
        return


    locations_map_filename = argv[0]
    read_locations_map(locations_map_filename)

    print('walk_dir = ' + walk_dir)

    xml_p = re.compile("<Location><o>(.*?)</o></Location>")
    compose_p = re.compile('attr_\d+_Location="(.*?)"')

    for file_num, (file, total_num_lines) in enumerate(loc_files):
        result_file = 'groups' + str(file_num) + '.txt'
        with open(result_file, 'w') as out_f:
            with open(file, 'r') as f:
                print('On file', file)
                print('num_lines: %d' % total_num_lines)
                for line_num, line in enumerate(f):
                    repl_line = re.sub(compose_p, reform_location, line)
                    out_f.write(repl_line)

                    progress = line_num / total_num_lines * 100
                    sys.stderr.write("%s: %d%%   \r" % (file, progress))
                    sys.stderr.flush()

        print('Replaced: %s' % loc_replaced)
        print('Total: %s' % loc_total)


if __name__ == "__main__":
    main(sys.argv[1:])

