import os
import sys
import re

walk_dir = '/data/safe/livejournal.com/pure-texts'

print('walk_dir = ' + walk_dir)

p = re.compile("<Location><o>(.*?)</o></Location>")
sum = 0

with open(output, 'w') as out:
    for root, subdirs, files in os.walk(walk_dir):
        for file in files:
            if not file[-4:] == '.txt':
                break
            with open(os.path.join(root, file), 'r') as f:
                print('On file', file)
                for line in f:
                    all_locs = re.findall(p, line)
                    for loc in all_locs:
                        sum += 1
    out.write('\nTotal number of locations:')
    out.write(str(sum))


