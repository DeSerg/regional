import sys
from subprocess import call
import time

sys.path.insert(0, '../..')

import regional_dict.regional_dict_helper as rdh

def main(argv):
    start = time.time()
    result, lemma = rdh.lemma('поджешника')
    print('time spent: ' + str(time.time() - start))

    if result:
        print(lemma)
    else:
        print('Error: with message:\n%s' % lemma)





if __name__ == "__main__":
    main(sys.argv)