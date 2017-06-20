/data/bin/apply.sh . perl -ne 'if(/<Location>(.*?)<\/Location>/){print "$1\n";}'
sort user_source_locations.txt | uniq -c | sort -rnk1,1 > user_source_locations.txt.sorted.uniq
df
# пример сортировки большого файла
LC_ALL=C sort back1.out back2.out -T temp -S 8G -k1,3 > back.out.sorted 
# запуск dummy
./dummy.loc.pl ./toponims-utf8.txt < user_source_locations.txt.sorted.uniq
