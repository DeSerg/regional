"""
Исполняемый файл для формирования .json файлов с текстовыми данными по
имеющимся идентификаторам текстов

Параметры:
    json файл с идентификаторами
    корпус в xml (tntres)
    Размер чанка в Mb для обработки xml
    Название выходных json файлов

Пример:
    python pretty_regional_search_data.json tnt-subset.xml 512 text-content.json
"""

import sys
import regional_dict.content_extractor as cextractor


if __name__ == "__main__":
    args = sys.argv[1:]
    sys.exit(cextractor.run(args))
