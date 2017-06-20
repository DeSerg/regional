import os
import sys
import re

output = 'user_locations.txt'

p = re.compile("<Location><o>(.*?)</o></Location>")

Toponims = '../toponims-utf8/toponims_obtained.txt'
unique_locations = 'unique_locations.txt'
user_locations = set()
sum_var = 0


def obtain_location(location, useful):
    global sum_var
    toponims = location.split(',')
    for toponim in toponims:
        if toponim in user_locations:
            sum_var += 1
            useful.add(toponim)


def main():
    with open(Toponims) as inp:
        for line in inp:
            loc_list = line.split('\t', 1)
            if loc_list:
                location = loc_list[0]
                user_locations.add(location)


    with open(output, 'w') as out:
        with open(unique_locations, 'r') as f:
            useful = set()
            for line in f:
                obtain_location(line, useful)

        for toponim in useful:
            out.write(toponim + '\n')

        out.write('\nTotal number of user locations among all locations:')
        out.write(str(len(useful)))
        out.write('\nTotal number of user locations:')
        out.write(str(len(user_locations)))

if __name__ == "__main__":
    main()