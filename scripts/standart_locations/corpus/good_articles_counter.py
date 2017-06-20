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

def write_info(file, persons, locations, text):
    file.write('==================================\n')
    if persons:
        file.write('Persons:\n')
        file.write(persons[0])
        for person in persons[1:]:
            file.write(', ')
            file.write(person)
    if locations:
        file.write('\nLocations:\n')
        file.write(locations[0])
        for location in locations[1:]:
            file.write('\n')
            file.write(location)
    if text:
        file.write('\nText:\n')
        file.write(text)

    file.write('\n\n')

#walk_dir = '/data/safe/livejournal.com/pure-texts'
walk_dir = './'
output = 'good_articles.txt'

print('walk_dir = ' + walk_dir)

article_start = '<article>'
article_end = '</article>'
text_start = '<text><o>'
text_end = '</o></text>'
loc_re = re.compile("<Location><o>(.*?)</o></Location>")
person_re = re.compile("<person><o>(.*?)</o></person>")

good_article = 0

with open(output, 'w') as out:
    for root, subdirs, files in os.walk(walk_dir):
        for file in files:
            if not file[-4:] == '.txt':
                break
            with open(os.path.join(root, file), 'r') as f:
                print('On file', file)

                inside_article = False
                text_found = False
                location_found = False
                text = ''
                locations = []
                persons = []

                inside_text = False

                for line in f:
                    line_stripped = line.strip()
                    if line_stripped == article_start:
                        inside_article = True
                        continue
                    if line_stripped == article_end:
                        if locations and text:
                            good_article += 1
                            write_info(out, persons, locations, text)
                        inside_article = False
                        continue
                    
                    if line_stripped == text_start:
                        inside_text = True
                        continue

                    if line_stripped == text_end:
                        inside_text = False
                        continue

                    if inside_text:
                        text += line
                        continue


                    all_locs = re.findall(loc_re, line)
                    if all_locs:
                        for loc in all_locs:
                            locations.append(extract_location(loc))
                        continue

                    all_persons = re.findall(person_re, line)
                    if all_persons:
                        for person in all_persons:
                            persons.append(person.strip())
                        continue
                    


    out.write('\nTotal number of articles with text and location: ')
    out.write(str(good_article))


