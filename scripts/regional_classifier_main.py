import sys
import numpy as np

import regional_classifier.regional_classifier_prepare as rprepare
import regional_classifier.regional_classifier_classify as rclassify

def cross_classify():
    # six main tune parameters
    types = ['multivariate', 'log_multinomial'] # + 'multinomial'
    region_filenames = [
        '../data/classification/db_top_locs_50.txt',
        '../data/classification/db_locs_main.txt',
        # '../data/classification/db_locs_main_exp.txt'
        # '../data/classification/db_top_locs_10.txt',
        # '../data/classification/db_top_locs_20.txt',
    ]
    author_nums = [100, 500]
    feature_weightings = ['log_odds', 'IG', 'ambiguity', 'none']  # + 'weight' ''
    features_to_select_arr = [100, 200] # 500
    min_texts_lengths = [5000, 3000, 1000] # 20, 300,
    classifiers = ['NB', 'logistic', 'SVM'] # + 'sklearn_NB'

    # other parameters
    dict_filename = '../data/dictionary_29_05_2017.xlsx'
    train_json = '../data/classification/db_lj_corpus.json'

    for min_texts_len in min_texts_lengths:
        for region_filename in region_filenames:
            for classifier in classifiers:
                for feature_weighting in feature_weightings:
                    for type in types:
                        for author_num in author_nums:
                            for features_to_select in features_to_select_arr:
                                rclassify.run_parsed_ex(
                                    region_filename, dict_filename, train_json,
                                    type, author_num,
                                    feature_weighting, features_to_select,
                                    min_texts_len, classifier)
                                print('\n\n\n')



def cross_classify_old():
    # six main tune parameters
    types = ['multivariate', 'log_multinomial']  # + 'multinomial'
    region_filenames = [
        # '../data/classification/top_locs_10.txt',
        # '../data/classification/top_locs_20.txt',
        '../data/classification/top_locs_50.txt'
    ]
    author_nums = [100, 500]
    feature_weightings = ['log_odds', 'IG', 'ambiguity', 'none']  # + 'weight'
    features_to_select_arr = [100, 200]
    classifiers = ['NB', 'logistic', 'SVM']  # + 'sklearn_NB'

    # other parameters
    dict_filename = '../data/dictionary_29_05_2017.xlsx'
    train_json = '../data/classification/lj_for_classification.json'

    for region_filename in region_filenames:
        for classifier in classifiers:
            for feature_weighting in feature_weightings:
                for type in types:
                    for author_num in author_nums:
                        for features_to_select in features_to_select_arr:
                            rclassify.run_parsed(
                                region_filename, dict_filename, train_json,
                                type, author_num,
                                feature_weighting, features_to_select,
                                classifier, new_corpus=False)
                            print('\n\n\n')


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Pass 'prepare' or 'classify' as first argument")

    module, args = sys.argv[1], sys.argv[2:]
    if module == 'prepare':
        sys.exit(rprepare.run(args))
    elif module == 'classify':
        sys.exit(rclassify.run(args))
    elif module == 'cross_classify':
        cross_classify()
    elif module == 'cross_classify_old':
        cross_classify_old()




