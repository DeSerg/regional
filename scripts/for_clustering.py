import sys
import pandas as pd
import numpy as np

from locations import save_to_file

def make_count_matrix(cross_table_filename, index, threshold = 100):
    cross_table = pd.DataFrame.from_csv(cross_table_filename, sep = '\t')
    answer = _read_cross_table(cross_table)
    rows = [([loc] + [np.sum(row[index])] + row[index]) for loc, row in answer.items()]
    return list(filter(lambda x: x[1] >= threshold, rows))
    
def _read_cross_table(cross_table):        
    first_column = 8
    last_column = cross_table.columns.get_loc('Other Locs')
    answer = {cross_table.columns[j] : ([], [])
              for j in range(first_column, last_column, 2)}
    for i, (lemma, row) in enumerate(cross_table.iterrows()):
        for j in range(first_column, last_column, 2):
            curr = answer[cross_table.columns[j]]
            curr[0].append(row[j])
            curr[1].append(row[j+1])    
    return answer


if __name__ == '__main__':
    if len(sys.argv) != 4:
        sys.exit("Pass type (words or authors), cross_table filename and out filename)")
    type, infile, outfile = sys.argv[1:]
    assert type in ('words', 'authors')
    matrix = make_count_matrix(infile, 0 if type=='words' else 1, 100)
    save_to_file(outfile, matrix)
    
                 
