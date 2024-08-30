"""
This script is used to perform a grid search over the hyperparameters of the clustering algorithms.

Parameters:
    --did: dataset id (1-10)
    --dbname: database name
    --clustering: clustering method
    --verbose: verbose mode

Example:
    python autoconf_gridsearch.py --did 1 --dbname dbs/autoconf_gridsearch --clustering UniqueMappingClustering --verbose True
"""
import time
import os
import sys
import pandas as pd
from pyjedai.datamodel import Data
from pyjedai.vector_based_blocking import EmbeddingsNNBlockBuilding
from pyjedai.clustering import UniqueMappingClustering, ConnectedComponentsClustering, KiralyMSMApproximateClustering
from tqdm import tqdm
import numpy as np

# from optuna.study import MaxTrialsCallback
# from optuna.trial import TrialState

import argparse

# ------------------------------- DATA ------------------------------- #
D1CSV = [
    "rest1.csv", "abt.csv", "amazon.csv", "dblp.csv",  "imdb.csv",  "imdb.csv",  "tmdb.csv",  "walmart.csv",   "dblp.csv",    "imdb.csv"
]
D2CSV = [
    "rest2.csv", "buy.csv", "gp.csv",     "acm.csv",   "tmdb.csv",  "tvdb.csv",  "tvdb.csv",  "amazon.csv",  "scholar.csv", "dbpedia.csv"
]
GTCSV = [
    "gt.csv",   "gt.csv",   "gt.csv",     "gt.csv",   "gt.csv", "gt.csv", "gt.csv", "gt.csv", "gt.csv", "gt.csv"
]
D = ['D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'D7', 'D8', 'D9','D10']

separator = [
    '|', '|', '#', '%', '|', '|', '|', '|', '>', '|'
]
engine = [
    'python', 'python','python','python','python','python','python','python','python', None
]
# -------------------------------  DATA END  ------------------------------- #

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('--did', type=int, default=-1)
parser.add_argument('--dbname', type=str, default=-1)
parser.add_argument('--clustering', type=str, default=None)
parser.add_argument('--verbose', type=bool, default=False)

did = parser.parse_args().did
db_name= parser.parse_args().dbname
clustering = parser.parse_args().clustering
verbose = parser.parse_args().verbose

# ------------------------------- EXPERIMENTS CONFIGURATION ------------------------------- #

CLUSTERING_MAPPING = {
    "UniqueMappingClustering": UniqueMappingClustering,
    "KiralyMSMApproximateClustering": KiralyMSMApproximateClustering,
    "ConnectedComponentsClustering": ConnectedComponentsClustering,
}

SEARCH_SPACE = {
    "threshold": np.arange(0.05, 0.95+0.05, 0.05),
    'k': range(1, 100+1, 1),
    'lm': ["smpnet", "st5", "sdistilroberta", "sminilm", "sent_glove", 'fasttext', 'word2vec'],
    "clustering" : list(CLUSTERING_MAPPING.keys())
}

DB_NAME = "autoconf_gridsearch" if db_name == -1 else db_name
STORAGE_NAME = "sqlite:///{}.db".format(DB_NAME)
SEED = 42
CSV_FILE_COLUMNS = 'trial,dataset,clustering,lm,k,threshold,sampler,seed,precision,recall,f1,runtime\n'
DESTINATION_FOLDER = 'results/gridsearch/'
DATA_DIR = '../data/'
PYJEDAI_TQDM_DISABLE = True
NUM_OF_TRIALS = len(SEARCH_SPACE["threshold"]) * len(SEARCH_SPACE["k"]) * len(SEARCH_SPACE['lm']) * len(SEARCH_SPACE["clustering"])
CSV_FILE_NAMES = [d+'.csv' for d in D]
OUTPUT_EXCEL_FILE_NAME = 'gridsearch.xlsx'
SAMPLER = 'gridsearch'
# ------------------------------- EXPERIMENTS CONFIGURATION END ------------------------------- #


print("\nConfiguration report:")
print("Number of LMs: ", len(SEARCH_SPACE['lm']))
print("Number of thresholds: ", len(SEARCH_SPACE['threshold']))
print("Number of Ks: ", len(SEARCH_SPACE['k']))
print("Number of clustering methods: ", len(SEARCH_SPACE['clustering']))
print("Total number of trials: ", NUM_OF_TRIALS)


for i in range(0,len(D)):
    
    if did != -1:
        i = did-1
    
    trial = 
    print("\n\nDataset: ", D[i])

    d = D[i]
    d1 = D1CSV[i]
    d2 = D2CSV[i]
    gt = GTCSV[i]
    s = separator[i]
    e = engine[i]

    with open(DESTINATION_FOLDER + d + '.csv', 'w') as f:
        f.write(CSV_FILE_COLUMNS)
        data = Data(
            dataset_1=pd.read_csv(DATA_DIR + d + "/" + d1 , 
                                sep=s,
                                engine=e,
                                na_filter=False).astype(str),
            id_column_name_1='id',
            dataset_name_1=d+"_"+d1.split(".")[0],
            dataset_2=pd.read_csv(DATA_DIR + d + "/" + d2 , 
                                sep=s, 
                                engine=e,
                                na_filter=False).astype(str),
            id_column_name_2='id',
            dataset_name_2=d+"_"+d2.split(".")[0],
            ground_truth=pd.read_csv(DATA_DIR + d + "/gt.csv", sep=s, engine=e))

        if verbose:
            data.print_specs()

        study_name = title  = d
        
        for lm in SEARCH_SPACE['lm']:
            for k in SEARCH_SPACE['k']:

                t1 = time.time()
                emb = EmbeddingsNNBlockBuilding(vectorizer=lm, similarity_search='faiss')

                blocks, g = emb.build_blocks(data,
                                            top_k=k,
                                            load_embeddings_if_exist=True,
                                            save_embeddings=True,
                                            tqdm_disable=PYJEDAI_TQDM_DISABLE,
                                            with_entity_matching=True)
                emb.evaluate(blocks, verbose=verbose)

                embeddings_time = time.time() - t1

                for clustering_method in SEARCH_SPACE['clustering']:
                    for threshold in SEARCH_SPACE['threshold']:
                        
                        t2 = time.time()
                        ccc = CLUSTERING_MAPPING[clustering_method]()
                        clusters = ccc.process(g, data, similarity_threshold=threshold)
                        results = ccc.evaluate(clusters, with_classification_report=True, verbose=verbose)

                        clustering_time = time.time() - t2
                        f1, precision, recall = results['F1 %'], results['Precision %'], results['Recall %']

                        f1 = round(f1, 4)
                        precision = round(precision, 4)
                        recall = round(recall, 4)

                        f.write('{},{},{},{},{},{},{},{},{},{},{},{}\n'.format(trial.number, d, clustering_method, lm, k, threshold, SAMPLER, SEED, precision, recall, f1, embeddings_time+clustering_time))
                        f.flush()

        f.close()
        
        if did != -1:
            break

with pd.ExcelWriter(OUTPUT_EXCEL_FILE_NAME, engine='openpyxl') as writer:
    for csv_file in CSV_FILE_NAMES:
        df = pd.read_csv(DESTINATION_FOLDER + csv_file)
        sheet_name = csv_file.rsplit('.', 1)[0]
        df.to_excel(writer, sheet_name=sheet_name, index=False)
