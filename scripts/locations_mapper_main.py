"""
Исполняемый файл для формирования словаря Руслана с колонкой
стандратизованных локаций

Параметры:
    csv файл с отображением между локациями в словаре Руслана и toponyms-utf8
    xlsx словарь Руслана с приведенными в нормальную форму локациями (без I, a) и т.п.)
    Название файла для выходного словаря Руслана со стандратизованными локациями

Пример:
    python ruslans_toponyms_map_hand.csv dictionary_20_11_2014.xlsx dictionary_13_12_4.xlsx
"""

import sys
import locations.locations_mapper as lmapper


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit('pass map')

    module = sys.argv[1]
    args = sys.argv[2:]
    if module == 'map':
        sys.exit(lmapper.run(args))
