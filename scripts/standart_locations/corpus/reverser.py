unique_filename = 'all_unuqie_locations.txt'
unique_filename_r = 'all_unique_locations_r.txt'

lines = []
with open(unique_filename) as unique_f:
    for line in unique_f:
        lines.append(line)

with open(unique_filename_r, 'w') as unique_f:
    for line in lines[::-1]:
        unique_f.write(line)