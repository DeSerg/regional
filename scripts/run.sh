#!/bin/bash
if [ "$#" -ne 7 ] ; then
	echo "$#"
	echo "Pass python script, corpus, dictionary file, chunk size, minimal words number for an author, output authors file and output texts file"
fi
echo "Reading..."
python3.3 -u $1 collect $2 $3 texts_tmp_1 $6 $4 $5
echo "Prettifying..."
python3.3 -u $1 pretty texts_tmp_1 lj $7
echo "Terminating..."
rm texts_tmp_1
#python3.3 -u $1 clean authors_tmp_1 texts_tmp_2 $5 $6 $7
#rm texts_tmp_2
#rm authors_tmp_1
