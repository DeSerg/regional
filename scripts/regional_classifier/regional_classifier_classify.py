import sys
import json
from collections import defaultdict
from itertools import chain
import bisect
import copy
import warnings
import getopt

import numpy as np
import scipy.sparse as scsp
from numpy import nanmean
import sklearn.metrics as skm
import sklearn.model_selection as skcv
from sklearn.utils.extmath import safe_sparse_dot

import sklearn.naive_bayes as sknb
import sklearn.linear_model as sklm
import sklearn.svm as sksvm

# from sklearn.base import BaseEstimator, ClassifierMixin
sys.path.insert(0, '..')
additional_loc_filename = '../data/additional_mapping.csv'

import regional_dict.regional_dict_helper as rdh
import regional_dict.regional_json_statistics as rjs
import location_utils.location_helper as lh
import corpus.corpus_helper as ch
from utility import routines as routines

np.set_printoptions(precision=3, suppress=True)
warnings.filterwarnings("ignore")


def prepare_data(classify_mode, process_mode, dict_filename,
                 regions_filename, authors_number, data_filename):
    lemmatizer = rdh.RegionalWords(dict_filename)
    locs_keys = lemmatizer.locs_list()
    admissible_locs = rjs.make_admissible_locations(locs_keys, additional_loc_filename)
    region_map = _read_regions(regions_filename)
    REGIONS_NUMBER = len(region_map)
    word_codes, lemma_codes = _make_regional_words_codes(lemmatizer.word_forms())
    nfeat = len(lemma_codes)

    json_data = json.load(open(data_filename, "r"))
    if classify_mode == 'texts':
        unregional_texts_counts = [0] * len(region_map)
        nrows, rows, cols, data, weights, y = 0, [], [], [], [], []
    elif classify_mode == 'authors':
        data, y = [], []
    ids = []
    author_indexes_by_regions = [[] for r in range(REGIONS_NUMBER)]
    for i, (author, elem) in enumerate(json_data.items()):
        loc = rjs.extract_loc(elem['loc'], admissible_locs)
        texts, unregional_texts_count = elem['texts'], elem['texts without regional']
        loc_code = region_map.get(loc, None)
        if loc_code is None:
            continue
        score = len(set(word_codes[word] for word in chain.from_iterable(texts)))
        author_indexes_by_regions[loc_code-1].append((author, score))
    for r in range(REGIONS_NUMBER):
        author_indexes_by_regions[r].sort(key = lambda x: x[1], reverse=True)
        author_indexes_by_regions[r] = author_indexes_by_regions[r][:authors_number]
    authors = list(x[0] for x in chain.from_iterable(author_indexes_by_regions))
    for i, author in enumerate(authors):
        elem = json_data[author]
        loc = rjs.extract_loc(elem.get('loc'), admissible_locs)
        texts, unregional_texts_count = elem.get('texts'), elem.get('texts without regional')
        loc_code = region_map.get(loc, None)
        if loc_code is None:
            continue
        author_lemma_counts = []
        for text in texts:
            lemma_counts = defaultdict(int)
            for word in text:
                lemma_counts[word_codes[word]] += 1
            author_lemma_counts.append(lemma_counts)
        if classify_mode == 'texts':
            for j, lemma_counts in enumerate(author_lemma_counts):
                for code, count in lemma_counts.items():
                    rows.append(nrow)
                    cols.append(code)
                    values.append(count)
                    weights.append(1.0)
                    y.append(loc_code)
                    ids.append(author + "_" + str(j))
                    nrows += 1
            unregional_texts_counts[loc_code-1] += unregional_texts_count
        elif classify_mode == 'authors':
            values, rows, cols, weights = [], [], [], []
            for i, lemma_counts in enumerate(author_lemma_counts):
                for code, count in lemma_counts.items():
                    rows.append(i)
                    cols.append(code)
                    values.append(count)
                weights.append(1.0)
            nrows = len(texts)
            if unregional_texts_count > 0:
                weights.append(unregional_texts_count)
                nrows += 1
            data.append((scsp.csr_matrix((values, (rows, cols)),
                                         shape=(nrows, nfeat), dtype=int),
                         weights))
            ids.append(author)
            y.append(loc_code)
    if classify_mode == 'texts':
        if process_mode == 'train':
            for code, count in enumerate(unregional_texts_counts, 1):
                weights.append(count)
                y.append(code)
                ids.append(str(nrows))
                nrows += 1
        data = scsp.csr_matrix((values, (rows, cols)), shape=(nrows, nfeat), dtype=int)
    return {'data': data, 'weights': weights, 'y': y, 'ids': ids,
            'region map': region_map, 'lemma codes': lemma_codes}


def prepare_data_db(classify_mode, process_mode, dict_filename,
                 regions_filename, authors_number, min_texts_len, data_filename):
    lemmatizer = rdh.RegionalWords(dict_filename)

    # locs_keys = lemmatizer.locs_list()
    # regions_keys = lemmatizer.regions_list()
    # countries_keys = lemmatizer.countries_list()

    region_map, country_map = _read_locs_db(regions_filename)
    REGIONS_NUMBER = len(region_map)
    COUNTRIES_NUMBER = len(country_map)
    word_codes, lemma_codes = _make_regional_words_codes(lemmatizer.word_forms())
    nfeat = len(lemma_codes)

    json_data = json.load(open(data_filename, "r"))
    if classify_mode == 'texts':
        unregional_texts_counts = [0] * len(region_map)
        nrows, rows, cols, data, weights, y = 0, [], [], [], [], []
    elif classify_mode == 'authors':
        data, y = [], []
    ids = []

    authors = _top_authors(REGIONS_NUMBER, COUNTRIES_NUMBER, json_data, region_map, country_map, authors_number, min_texts_len)

    for i, author in enumerate(authors):
        elem = json_data[author]
        loc, loc_code, loc_type = _extract_loc(elem, region_map, country_map)
        if loc_code is None:
            continue

        texts, unregional_texts_count = elem[lh.PositiveTextsKey], elem[lh.NegativeTextsNumKey]

        author_lemma_counts = []
        for text in texts:
            lemma_counts = defaultdict(int)
            for lemma in text:
                lemma_counts[lemma_codes[lemma]] += 1
            author_lemma_counts.append(lemma_counts)

        if classify_mode == 'texts':
            for j, lemma_counts in enumerate(author_lemma_counts):
                for code, count in lemma_counts.items():
                    rows.append(nrows)
                    cols.append(code)
                    values.append(count)
                    weights.append(1.0)
                    y.append(loc_code)
                    ids.append(author + "_" + str(j))
                    nrows += 1
            unregional_texts_counts[loc_code-1] += unregional_texts_count
        elif classify_mode == 'authors':
            values, rows, cols, weights = [], [], [], []
            for i, lemma_counts in enumerate(author_lemma_counts):
                for code, count in lemma_counts.items():
                    rows.append(i)
                    cols.append(code)
                    values.append(count)
                weights.append(1.0)
            nrows = len(texts)
            if unregional_texts_count > 0:
                weights.append(unregional_texts_count)
                nrows += 1
            data.append((scsp.csr_matrix((values, (rows, cols)),
                                         shape=(nrows, nfeat), dtype=int),
                         weights))
            ids.append(author)
            y.append(loc_code)

    if classify_mode == 'texts':
        if process_mode == 'train':
            for code, count in enumerate(unregional_texts_counts, 1):
                weights.append(count)
                y.append(code)
                ids.append(str(nrows))
                nrows += 1
        data = scsp.csr_matrix((values, (rows, cols)), shape=(nrows, nfeat), dtype=int)
    return {'data': data, 'weights': weights, 'y': y, 'ids': ids,
            'region map': region_map, 'lemma codes': lemma_codes}


def _top_authors(rn_num, cn_num, json_data, rn_map, cn_map, authors_number, min_texts_len):
    loc_num = rn_num + cn_num
    author_indexes_by_loc = [[] for r in range(rn_num + cn_num)]

    for i, (author, elem) in enumerate(json_data.items()):
        if lh.TextsLenKey in elem:
            texts_len = elem[lh.TextsLenKey]
            if texts_len < min_texts_len:
                continue

        loc, loc_code, loc_type = _extract_loc(elem, rn_map, cn_map)
        if loc_code is None:
            continue

        texts, unregional_texts_count = elem[lh.PositiveTextsKey], elem[lh.NegativeTextsNumKey]

        score = len(texts)
        author_indexes_by_loc[loc_code - 1].append((author, score))

    for i in range(loc_num):
        author_indexes_by_loc[i].sort(key = lambda x: x[1], reverse=True)
        author_indexes_by_loc[i] = author_indexes_by_loc[i][:authors_number]

    return list(set((x[0] for x in chain.from_iterable(author_indexes_by_loc))))

def _extract_loc(data, region_map, country_map):
    region = ''
    region_code = None
    country = ''
    country_code = None

    if lh.RegionKey in data:
        region = data[lh.RegionKey]
        region_code = region_map.get(region, None)
    if lh.CountryKey in data:
        country = data[lh.CountryKey]
        country_code = country_map.get(country, None)

    if not region_code is None:
        return region, region_code, 'rn'

    return country, country_code, 'cn'

def _read_regions(filename):
    answer = dict()
    with open(filename, "r") as infile:
        for code, line in enumerate(infile, 1):
            line = line.strip()
            answer[line] = code
    return answer

def _read_locs_db(filename):
    regions = dict()
    countries = dict()
    with open(filename, "r") as infile:
        for code, line in enumerate(infile, 1):
            line = line.strip()
            if not line:
                continue
            line_split = line.split(': ')
            if len(line_split) != 2:
                print(line)
            assert(len(line_split) == 2)
            loc_level, loc_name = line_split[0], line_split[1]
            if loc_level == lh.RegionKey:
                regions[loc_name] = code
            else:
                countries[loc_name] = code
    return regions, countries

def _make_regional_words_codes(words_dict):
    lemma_codes = {lemma: i for (i, lemma) in enumerate(set(words_dict.values()))}
    word_codes = {word.strip(): lemma_codes[lemma] for (words, lemma) in words_dict.items() for word in words.split(';') }
    return word_codes, lemma_codes


class RegionalBayesClassifier:

    def __init__(self, mode, classifier='NB', algorithm='simple', type='multivariate',
                 alpha=1.0, feature_weighting=None, local=False):
        self.mode = mode
        self.classifier = classifier
        self.algorithm = algorithm
        self.type = type
        self.alpha = alpha
        self.selection = feature_weighting
        self.is_selection_local = local

    def fit(self, X, y, to_select=-1):
        self._check_parameters()
        if len(X) == 0:
            raise ValueError("Cannot fit on empty data")
        if self.mode == 'texts':
            N, nfeat = X.shape
        elif self.mode == 'authors':
            N, nfeat = len(X), X[0][0].shape[1]

        self.classes_, y = np.unique(y, return_inverse=True)
        nclasses = self.classes_.shape[0]
        Y_new = np.zeros(shape=(N, nclasses), dtype=int)
        Y_new[np.arange(N), y] = 1

        X_new, weights = self._preprocess(X)
        self.sparse = scsp.issparse(X_new)
        if not self.sparse:
            raise NotImplementedError("Dense version is not implemented yet")
        self.counts = safe_sparse_dot(Y_new.T, X_new)
        self.classes_counts = np.sum(Y_new.T * weights, axis=1)
        # removing idle features
        self.indices = self.make_feature_mask(to_select)
        X_new = self.select_features(X_new)
        # selecting features sholud preceed count modification
        if self.type == 'log_multinomial':
            if self.sparse:
                X_new.data = np.log2(1.0 + X_new.data)
            else:
                X_new = 1.0 + X_new
            weights = np.log2(1.0 + weights)
            self.counts = safe_sparse_dot(Y_new.T, X_new)
            self.classes_counts = np.sum(Y_new.T * weights, axis=1)
        X_new = self._normalize_data(X_new, weights)
        self._fit_model(X_new, y)
        if self.selection in ['weight','absolute_weight']:
            if self.classifier == 'NB':
                scores = self.weights
            else:
                scores = self.classifier.coef_
            if self.selection =='absolute_weight':
                scores = np.abs(scores)
            self.indices = self.calculate_best_features(scores, to_select)
            X_new = self.select_features(X_new)
            self._fit_model(X_new, y)
        return self

    def _fit_NB(self):
        nclasses = self.classes_.shape[0]
        self.probs = ((self.counts + self.alpha) /
                      (self.classes_counts + 2.0 * self.alpha).reshape((nclasses, 1)))
        if self.algorithm == 'simple':
            self.weights = np.log(self.probs)
        elif self.algorithm == 'rennie':
            self.weights = np.log(self.probs)
            self.weights /= np.sum(np.abs(self.weights), axis=1).reshape(nclasses, 1)
        return self

    def _fit_model(self, X, y):
        if self.classifier == 'NB':
            self.model = None
            self._fit_NB()
        elif self.classifier == 'sklearn_NB':
            if self.type == 'multivariate':
                self.model = sknb.BernoulliNB(alpha=self.alpha, fit_prior=False, class_prior=None)
            else:
                self.model = sknb.MultinomialNB(alpha=self.alpha, fit_prior=False, class_prior=None)
            self.model.fit(X, y)
        elif self.classifier == 'logistic':
            self.model = sklm.LogisticRegression(penalty='l2', C=1.0, class_weight='auto')
            self.model.fit(X, y)
        elif self.classifier == 'SVM':
            self.model = sksvm.SVC(C=1.0, kernel='linear', class_weight='auto', probability=True)
            self.model.fit(X, y)
        return self

    def make_feature_mask(self, to_select):
        _, nfeat = self.counts.shape
        if (to_select == -1 or to_select >= nfeat or
            self.selection in [None, "none", "weight", "absolute_weight"]):
            return np.arange(self.counts.shape[1])
        feature_weights = self.calculate_feature_weights()
        return self.calculate_best_features(feature_weights, to_select)

    def calculate_best_features(self, feature_weights, to_select):
        if self.is_selection_local:
            feature_indexes = np.argsort(feature_weights, axis=1)[:, ::-1]
            selected = set()
            for i in range(feature_indexes.shape[1]):
                selected |= set(feature_indexes[:, i])
                if len(selected) >= to_select:
                    break
        else:
            feature_indexes = np.argsort(feature_weights)[::-1]
            selected = feature_indexes[:to_select]
        return sorted(selected)

    def calculate_feature_weights(self):
        if self.is_selection_local:
            feature_weights = np.zeros(shape=self.counts.shape, dtype=np.float64)
            nclasses, nfeat = self.counts.shape
            N = np.sum(self.classes_counts)
            feature_counts_sums = np.sum(self.counts, axis=0)
            if self.selection in ['log_odds', 'IG']:
                contingency_tables = np.zeros(shape=(nclasses, nfeat, 2, 2), dtype=np.float64)
                for i in range(nclasses):
                    for j in range(nfeat):
                        count, feature_count, class_count =\
                            self.counts[i,j], feature_counts_sums[j], self.classes_counts[i]
                        rest = N - feature_count - class_count + count
                        contingency_tables[i][j] = [[count, feature_count - count],
                                                    [class_count - count, rest]]
                if self.selection == 'log_odds':
                    func = (lambda x: routines.odds_ratio(x, alpha=0.1))
                else:
                    func = routines.information_gain
                for i in range(nclasses):
                    for j in range(nfeat):
                        # print (contingency_tables[i][j])
                        feature_weights[i][j] = func(contingency_tables[i][j])
            elif self.selection == 'ambiguity':
                for i in range(nclasses):
                    for j in range(nfeat):
                        count, feature_count = self.counts[i,j], feature_counts_sums[j]
                        feature_weights[i][j] = (count / feature_count) if count >= 3.0 else 0.0
        else:
            if self.selection == "log_odds":
                raise ValueError("Impossible to apply log_odds for global selection")
            raise NotImplementedError()
        return feature_weights

    def select_features(self, X, train=True):
        N, nfeat = X.shape
        if len(self.indices) == nfeat:
            return X
        new_indices = {index: i for i, index in enumerate(self.indices)}
        if self.sparse:
            X = scsp.csr_matrix(X)
            X.eliminate_zeros()
            data, (rows, cols) = X.data, X.nonzero()
            indices = [i for i, j in enumerate(cols) if j in new_indices]
            X = scsp.csr_matrix((data[indices], (rows[indices],
                                 [new_indices[j] for j in cols[indices]])),
                                shape=(N, len(self.indices)), dtype=X.dtype)
        else:
            X = X[:, self.indices]
        if train:
            self.counts = self.counts[:, self.indices]
        return X

    def decision_function(self, X):
        X_new = self._transform_data(X)
        if self.classifier == 'NB':
            return safe_sparse_dot(X_new, self.weights.T)
        else:
            if hasattr(self.model, "decision_function"):
                return self.model.decision_function(X)
            elif hasattr(self.model, "decision_function"):
                return self.model.predict_proba(X)
            else:
                raise NotImplementedError(
                    "Decision function is not implemented fot the classifier")

    def predict(self, X):
        if self.classifier == 'NB':
            indices = np.argmax(self.decision_function(X), axis=1)
        else:
            X_new = self._transform_data(X)
            indices = self.model.predict(X_new)
        return np.take(self.classes_, indices)

    def predict_proba(self, X):
        if self.classifier == 'NB':
            return self._predict_proba_NB(X)
        else:
            X_new = self._transform_data(X)
            return self.model.predict_proba(X_new)

    def _predict_proba_NB(self, X):
        if self.algorithm == 'rennie':
            raise NotImplementedError("Probabilities are not implemented for Rennie algorithm")
        THRESHOLD = 5.0
        scores, n = self.decision_function(X), X.shape[0]
        scores -= np.max(scores, axis=1).reshape((n, 1))
        for_probs = np.where(scores > -THRESHOLD, np.exp(scores), 0.0)
        return for_probs / np.sum(for_probs, axis=1).reshape((n, 1))

    def _check_parameters(self):
        if self.mode not in ['authors', 'texts']:
            raise ValueError("mode should be 'authors' or 'texts'")
        if self.classifier in ['NB', 'sklearn_NB']:
            self.normalize = False
        elif self.classifier in ['logistic', 'SVM']:
            self.normalize = False
        else:
            raise ValueError("classifier should be of ['NB', 'sklearn_NB', 'logistic', 'SVM']")
        if self.algorithm not in ['simple', 'rennie']:
            raise ValueError("algorithm should be 'simple' or 'rennie'")
        if self.type not in ['multivariate', 'multinomial', 'log_multinomial']:
            raise ValueError("Type should be one of "
                             "['multivariate', 'multinomial', 'log_multinomial']")

    def _preprocess(self, X):
        data, rows, cols, weights = [], [], [], []
        if self.mode == 'texts':
            raise NotImplementedError
        elif self.mode == 'authors':
            for i, (x, x_weights) in enumerate(X):
                _, nfeat = x.shape
                if self.type == 'multivariate':
                    author_counts = ((x.max(axis=0)) > 0).toarray()
                    weight = 1.0
                elif self.type in ['multinomial', 'log_multinomial']:
                    repeated_weights =\
                        np.array(x_weights).reshape(x.shape[0], 1).repeat(repeats=nfeat, axis=1)
                    author_counts = (x.toarray().T * x_weights).sum(axis = 1)
                    weight = np.sum(x_weights)
                author_counts = author_counts.reshape((nfeat,))
                for j, count in enumerate(author_counts):
                    if count > 0.0:
                        data.append(count)
                        rows.append(i)
                        cols.append(j)
                weights.append(weight)
            X_new = scsp.csr_matrix((data, (rows, cols)),
                                    shape=(X.shape[0], nfeat), dtype=np.float32)
            return X_new, np.array(weights)

    def _normalize_data(self, X, weights):
        if self.type in ['multinomial', 'log_multinomial'] and self.normalize:
            # we do not need to normalize counts for multivariate model
            if self.sparse:
                X.eliminate_zeros()
                rows, cols = X.nonzero()
                X.data = np.fromiter(((value / weights[i]) for (value, i) in zip(X.data, rows)),
                                     dtype=X.dtype)
            else:
                X = (X.T * weights).T
        return X

    def _transform_data(self, X):
        X_new, weights = self._preprocess(X)
        X_new = self.select_features(X_new, train=False)
        if self.type == 'log_multinomial':
            if self.sparse:
                X_new.data = np.log2(1.0 + X_new.data)
            else:
                X_new = 1.0 + X_new
        X_new = self._normalize_data(X_new, weights)
        return X_new


def _calculate_first_positions(a, labels):
    if len(labels) == 0:
        return []
    positions, count, total_number = dict(), 0, len(labels)
    for i, x in enumerate(a):
        if x in labels and x not in positions:
            positions[x] = i
            count += 1
            if count == len(labels):
                break
    return [positions.get(x, None) for x in labels]

class PercentageCalculator:
    def __init__(self, score_func, labels):
        self.score_func = score_func
        self.labels = labels
        self.label_codes ={label : i for i, label in enumerate(self.labels)}

    def fit(self, test, pred, probs, thresholds):
        test, pred, probs = np.asarray(test), np.asarray(pred), np.asarray(probs)
        n = test.shape[0]
        if test.shape[0] != n or test.shape[0] != n:
            raise ValueError("Test, pred and probs should be of equal length")
        self.thresholds = sorted(thresholds, reverse=True)
        order = np.argsort(probs)
        sorted_probs = np.take(probs, order)
        threshold_positions = [bisect.bisect_left(sorted_probs, threshold)
                               for threshold in self.thresholds]
        order = order[::-1]
        test, pred = test.take(order), pred.take(order)
        threshold_positions = [n - t for t in threshold_positions]
        if threshold_positions[-1] != n:
            threshold_positions.append(n)
            self.thresholds.append(sorted_probs[0])
        self.counts = np.zeros(shape=(len(threshold_positions), len(self.labels)),
                               dtype=int)
        self.scores = np.zeros(shape=(len(threshold_positions), len(self.labels)),
                               dtype=np.float64)
        threshold_index = 0
        for i, (pos, label) in enumerate(zip(order, test)):
            while i == threshold_positions[threshold_index]:
                threshold_index += 1
            label_code = self.label_codes[label]
            self.counts[threshold_index][label_code] += 1
        self.counts = np.cumsum(self.counts, axis=0)
        for i, t in enumerate(threshold_positions):
            self.scores[i] = self.score_func(test[:t], pred[:t],
                                             labels=self.labels, average=None)
            self.scores[i] = np.where(self.counts[i] > 0, self.scores[i], np.nan)
        return self

def run(args):
    try:
        optlist, args = getopt.getopt(args, 'ls', ['local'])
    except getopt.GetoptError as err:
        sys.exit(err)
    local = False
    for opt, a in optlist:
        if opt in ['-l', '--local']:
            local = True

    if len(args) != 11:
        print (args)
        sys.exit('''Usage:
                 regions_filename (list of locations),
                 dict_filename (Ruslan's region words),
                 train_json_file (json corpus),
                 type('multivariate', 'multinomial'),
                 authors_number (number of top authors for each location),
                 feature_weighting ('log_odds', 'IG', 'weight', 'absolute_weight', 'ambiguity', 'none'),
                 features_to_select (number),
                 classifier ('sklearn_NB', 'NB', 'logistic', 'SVM'),
                 algorithm('simple' or 'rennie'), ,
                 mode('authors' or 'texts'),  
                 n_folds (number of folds),
                 [-l] (local)''')

    regions_filename, dict_filename, train_json, type, authors_number = args[:5],
    feature_weighting, features_to_select, classifier, algorithm = args[5:9]
    mode, nfolds = args[9:]
    authors_number, features_to_select, nfolds = int(authors_number), int(features_to_select), int(nfolds)
    run_parsed(regions_filename, dict_filename, train_json, type,
               authors_number, feature_weighting, features_to_select,
               classifier, algorithm, mode, nfolds, local)


def run_parsed(regions_filename, dict_filename, train_json,
               type = 'multivariate', authors_number = 100,
               feature_weighting ='log_odds', features_to_select = 100,
               min_texts_len=ch.MinTextLen, classifier ='NB',
               algorithm = 'simple', mode = 'authors', nfolds = 10, local=True, new_corpus=True):

    clf = RegionalBayesClassifier(mode=mode, classifier=classifier, algorithm=algorithm, type=type,
                                  alpha=0.1, feature_weighting=feature_weighting, local=local)

    if new_corpus:
        data = prepare_data_db(mode, 'train', dict_filename, regions_filename, authors_number, min_texts_len, train_json)
    else:
        data = prepare_data(mode, 'train', dict_filename, regions_filename, authors_number, train_json)

    X, y, authors = data['data'], data['y'], data['ids']
    X, y = np.array(X, dtype='object'), np.array(y, dtype='int32')
    labels = sorted(set(y))
    n_classes = len(labels)
    shuf_split = skcv.StratifiedShuffleSplit(n_splits=nfolds, test_size=0.2, random_state=217)
    indices = shuf_split.split(X, y)
    counts, scores = [0] * nfolds, [0.0] * nfolds

    for j, (train, test) in enumerate(indices):
        X_train, X_test = X[train], X[test]
        y_train, y_test = y[train], y[test]
        curr_clf = copy.deepcopy(clf).fit(X_train, y_train, features_to_select)
        probs = curr_clf.predict_proba(X_test)
        max_indices = np.argmax(probs, axis=1)
        y_pred = np.take(curr_clf.classes_, max_indices)
        max_probs = probs[np.arange(max_indices.shape[0]), max_indices]

        calculator = PercentageCalculator(skm.precision_score, labels)
        prob_thresholds = [0.5, 0.75, 0.9]
        calculator.fit(y_test, y_pred, max_probs, prob_thresholds)
        counts[j], scores[j], thresholds = \
            calculator.counts, calculator.scores, calculator.thresholds
    test_size = np.mean([len(test) for train, test in indices])
    counts = np.mean(np.asarray(counts), axis=0)
    scores = np.mean(np.asarray(scores), axis=0)

    print('regions           : ' + regions_filename)
    print('classificator     : ' + classifier)
    print('feature weighting : ' + feature_weighting)
    print('model             : ' + type)
    print('authors number    : ' + str(authors_number))
    print('features to select: ' + str(features_to_select))
    for count, score, threshold in zip(counts, scores, thresholds):
        print("{0:<.1f} {1:<.1f} {2:<.2f}".format(
            100 * nanmean(score), 100 * np.sum(count) / test.size, threshold), end=" ")
        print("")
