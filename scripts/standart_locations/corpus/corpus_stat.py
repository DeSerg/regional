import os
import sys
import re

def extract_location(line):
    loc = line.split(',')

    if not loc:
        return ''

    loc = [s.strip() for s in loc]

    line_extr = loc[0]
    for loc_item in loc[1:]:
        line_extr = line_extr + ',' + loc_item
    return line_extr

loc_files = [
    ('/data/kaa/compose/m.lj.compact/groups.txt', 146425),
    ('/data/kaa/compose/m.lj.compact5/groups.txt', 585704),
    ('/data/kaa/compose/m.lj.compactR/groups.txt', 732129)
]

walk_dir = '/data/safe/livejournal.com/pure-texts'
output = 'all_unuqie_locations.txt'

print('walk_dir = ' + walk_dir)

xml_p = re.compile("<Location><o>(.*?)</o></Location>")
compose_p = re.compile('attr_\d+_Location="(.*?)"')

location_set = set()

TotalCounter = 0

with open(output, 'w') as out_f:
    for file, total_num_lines in loc_files:
        with open(file, 'r') as f:
            print('On file', file)
            print('num_lines: %d' % total_num_lines)
            for line_num, line in enumerate(f):
                all_locs = re.findall(compose_p, line)
                for loc in all_locs:
                    TotalCounter += 1
                    #print(loc)
                    loc_extr = extract_location(loc)
                    if not loc_extr in location_set:
                        location_set.add(loc_extr)
                        #print('=>', loc_extr)
                        out_f.write(loc_extr)
                        out_f.write('\n')

                progress = line_num / total_num_lines * 100
                sys.stderr.write("%s: %d%%   \r" % (file, progress))
                sys.stderr.flush()
    out_f.write('\nNumber of locations: %d\n' % len(location_set))
    out_f.write('Total number of locations: %d' % TotalCounter)



