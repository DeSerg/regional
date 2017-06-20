index_filename = '../../data/classification/index'


index_set = set()
with open(index_filename) as index_r:
    for line in index_r:
        line = line.strip()
        index_set.add(line)


with open(index_filename + '_out', 'w') as index_w:
    for word in index_set:
        index_w.write(word + '\n')