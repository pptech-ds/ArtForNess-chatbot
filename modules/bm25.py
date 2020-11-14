# -*- coding: utf-8 -*-
import pandas as pd 
from rank_bm25 import BM25Okapi
from modules.functions import build_keywords_list
from modules.functions import clean_text


# déclare les paramètres de l'IR dans un dict
arg_dict = {}
arg_dict['stopwords_csv'] = 'data_ir/stopwords.csv'
arg_dict['BM25_threshold'] = 0
arg_dict['BM25_nb_max_result'] = 5
arg_dict['tolerance'] = 0.01
arg_dict['language'] = 'french'
arg_dict['device'] = 'cpu'


def bm25_scoring(data_to_score, query):
    print("data file to score: {}".format(data_to_score))
    print("query: {}".format(query))

    #keeping only usefull keyword from given query
    query_keywords_list = build_keywords_list(arg_dict['stopwords_csv'], arg_dict['language'], str(query))

    #loading data csv to score into pandas dataframe 
    df = pd.read_csv(data_to_score)

    #declaring corpus array to give to BM25 to score
    corpus = []

    #building corpus
    for i in range(len(df)):
        #concatening all elements on one line together
        line_for_corpus = str(df.iloc[i]['Titre']).lower()+' '+str(df.iloc[i]['Descriptif']).lower()+' '+str(df.iloc[i]['Description']).lower()+' '+str(df.iloc[i]['Prix']).lower()+' '+str(df.iloc[i]['Categorie']).lower()+' '+str(df.iloc[i]['Etiquette']).lower()
        #cleaning text by removing accents and HTML balises
        line_for_corpus_clean = clean_text(line_for_corpus)
        #adding element to corpus
        corpus.append(line_for_corpus_clean)

    #running BM25 on corpus to get scores
    bm25 = BM25Okapi(corpus)

    #tokenizing query keywords
    tokenized_query = query_keywords_list.split(",")

    #get BM25 scores
    doc_scores = bm25.get_scores(tokenized_query)

    #defining a new column into pandas dataframe with scores
    df['score'] = doc_scores

    #sorting dataframe by scores, hightest to lowest
    df.sort_values(by=['score'], inplace=True, ascending=False)
   
    #dropping elements with score 0
    indexNames = df[df['score'] <= arg_dict['BM25_threshold'] ].index
    df.drop(indexNames , inplace=True)
    
    return df