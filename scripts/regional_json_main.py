    # -*- coding: utf8 -*-
"""
Исполняемый файл для формирования подкорпуса, который содержит словоформы
из словаря Руслана и работы с ним.

Параметры:
    type
        collect - модуль сбора счётчиков лексем в тексте
            корпус в xml (tntres)
            словарь со стандартизованными локациями
            Название выходного json файла с результатами сбора
            Название выходного json файла с первичной статистикой по авторам
            Размер чанка в Mb для обработки xml
        pretty - модуль приведения найденных данных в удобный и очищенный вид
            сформированный с помощью модуля поиска json файл
            Название выходного json файла
Пример:
     python3.3  ../scripts_py/regional_json_main.py stat authors
         pretty_word_search_results.json author_search_results.json regional_words_dump.json
         dictionary_13_12_2014.xlsx additional_mapping.csv 5000 authors_table_5000.csv

     python3.3 ../scripts_py/regional_json_main.py demonstrate  dictionary_13_12_2014.xlsx
         additional_mapping.csv cross_table_5000.csv locs_table_5000.csv results_new -1

"""

import sys
import regional_dict.regional_collect as rcollect
import regional_dict.regional_json_statistics as rstat
import regional_dict.regional_json_prettifyer as rpretty
#import regional_dict.regional_stats_demonstrator as rdemonstrate

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit('pass collect, pretty or clean as an argument')

    module = sys.argv[1]
    args = sys.argv[2:]
    if module == 'collect':
        sys.exit(rcollect.run(args))
    elif module == 'pretty':
        sys.exit(rpretty.run(args))
    elif module == 'stats':
        sys.exit(rstat.run(args))
