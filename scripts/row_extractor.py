import sys
import pandas as pd

def extract_data(etalon_infile, infile):
    etalon_data = pd.read_csv(etalon_infile, sep="\t", header=0)
    keys = set(etalon_data['Лемма'])
    input_data = pd.read_csv(infile, sep="\t", header=0)
    row_mask = [(elem in keys) for elem in input_data['Лемма']]
    return input_data[row_mask]


def output(data, outfile):
    data.to_csv(outfile, sep="\t")

if __name__ == '__main__':
    if len(sys.argv) != 4:
        sys.exit("Pass example csv file, input file and output file.")
    data_table = extract_data(sys.argv[1], sys.argv[2])
    output(data_table, sys.argv[3])
