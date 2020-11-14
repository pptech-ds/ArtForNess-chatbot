import unidecode
import re
import csv
import pandas as pd
import string
import json
import spacy
import requests
# import httplib2
# import urllib.request
# from urllib2 import urlopen


from string import punctuation

# s'assure que le paramètre passé est bien encodé en utf-8
def ensureUtf(s):
    try:
        if type(s) == unicode:
            return s.encode('utf8', 'ignore')
    except: 
        return str(s)


# enleve les accents du mot s'il y en a
def remove_accent(word):
    accented_string = ensureUtf(word)
    unaccented_string = unidecode.unidecode(accented_string)

    return unaccented_string


# remplace les accents html format par des accents normaux
def replace_html_accent(text):
    text1 = text.replace("&acirc;", "â")
    text2 = text1.replace("&agrave;", "à")
    text3 = text2.replace("&eacute;", "é")
    text4 = text3.replace("&ecirc;", "ê")
    text5 = text4.replace("&egrave;", "è")
    text6 = text5.replace("&euml;", "ë")
    text7 = text6.replace("&icirc;", "î")
    text8 = text7.replace("&iuml;", "ï")
    text9 = text8.replace("&ocirc;", "ô")
    text10 = text9.replace("&oelig;", "œ")
    text11 = text10.replace("&ugrave;", "û")
    text12 = text11.replace("&uuml;", "ü")
    text13 = text12.replace("&ccedil;", "ç")

    return text13


# clean le html en enlevant les balises
def clean_html(raw_html):
    cleanr = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')
    cleantext = re.sub(cleanr, '', raw_html)

    return cleantext


def define_custom_ponctuations(ponctuations):
    new_ponctuations = ''
    for i in range(len(ponctuations)):
        if(ponctuations[i] != "'"):
            new_ponctuations = new_ponctuations+ponctuations[i]
    
    return new_ponctuations

# clean le text en enlevant les symboles specifiques, les ponctuations
def clean_text(text):
    #print('in clean_text')
    # print('functions::clean_text: punctuation: {}'.format(punctuation))
    # print('functions::clean_text: define_custom_ponctuations(punctuation): {}'.format(define_custom_ponctuations(punctuation)))
    # print('functions::clean_text: type(punctuation): {}'.format(type(punctuation)))
    
    text_accent_fixed = replace_html_accent(text)
    char_to_remove = ['(',')','[',']','{','}']
    raw_text = clean_html(text_accent_fixed)
    text_punctation_removed = ''.join(c for c in raw_text if c not in define_custom_ponctuations(punctuation))
    text_whitespace_removed = text_punctation_removed.strip()
    text_replace_characters = ''.join(c for c in text_whitespace_removed if c not in char_to_remove)
    text_replace_characters_lower = text_replace_characters.lower()
    text_woaccent = tokenize_cleaned_text(text_replace_characters_lower)

    return text_woaccent



# tokenizer du text clean
def tokenize_cleaned_text(text):
    text_tokenized = text.split()
    text_tokenized_woaccent = []

    for i in range(len(text_tokenized)):
        text_tokenized_woaccent.append(remove_accent(text_tokenized[i]))
        # text_tokenized_woaccent.append(text_tokenized[i])

    return text_tokenized_woaccent


# definie le spacy tokenizer dependant du language
def define_spacy_tokenizer(language):
    # Construction 1
    from spacy.tokenizer import Tokenizer
    if(language == 'french'):
        from spacy.lang.fr import French
        nlp = French()
    if(language == 'english'):
        from spacy.lang.en import English
        nlp = English()
    # Create a blank Tokenizer with just the language vocab
    tokenizer = Tokenizer(nlp.vocab)

    return tokenizer


#Build keywords list from query
def build_keywords_list(stopwords_csv, language, query):

    keywords_list = build_keywords_list_spacy(language, query)

    keywords_list = keywords_list.strip()

    df_stopwords_csv = pd.read_csv(stopwords_csv, delimiter = ',') 
    
    stopwords_list = df_stopwords_csv[language].tolist()
    punctuations_list = string.punctuation

    tokenizer = define_spacy_tokenizer(language)
    tokens = tokenizer(keywords_list.lower())

    keywords_concat = ''

    for word in tokens:
        if((word.text not in stopwords_list) and (word.text not in punctuations_list)):
            if(keywords_concat != ''):
                keywords_concat = keywords_concat +','+word.text 
            else:
                keywords_concat = word.text

    print('functions::build_keywords_list: les mots cles de la requete: {}\n'.format(keywords_concat))

    return keywords_concat



#Build keywords list from query
def build_keywords_list_spacy(language, query):

    nlp = ''

    if(language == 'french'):
        nlp = spacy.load('fr_core_news_sm')
    elif(language == 'english'):
        nlp = spacy.load('en_core_web_sm')
    else:
        print('functions::build_keywords_list_spacy: Given language {} not defined in process build_keywords_list_spacy\n'.format(language))
        exit(1)

    print('functions::build_keywords_list_spacy: requete intiale: {}\n'.format(query))

    query_clean_tokens = tokenize_cleaned_text(query)

    query_clean = " ".join(query_clean_tokens)
    print('functions::build_keywords_list_spacy: requete clean: {}\n'.format(query_clean))

    doc = nlp(query_clean.lower())
    keywords_list = []

    for token in doc:
        if((token.pos_ == 'NOUN')):
            keywords_list.append(token.text)

            if('Number=Sing' in token.tag_):
                keywords_list.append(french_singular_to_plural(token.text))

            if('Number=Plur' in token.tag_):
                keywords_list.append(french_plural_to_singular(token.text))
        
        if((token.pos_ == 'VERB')):
            if((token.dep_ == 'ROOT')):
                keywords_list.append(token.text)

        if((token.pos_ == 'ADJ')):
            keywords_list.append(token.text)

        if((token.pos_ == 'PROPN')):
            keywords_list.append(token.text)
            
    print('token.text', 'token.pos_', 'token.dep_')
    for token in doc:
        print(token.text, token.pos_, token.dep_)

    keywords_concat = ''

    for word in keywords_list:
        keywords_concat = keywords_concat +' '+word 
        

    # print('build_keywords_list_spacy: Initial query string: {}\n'.format(doc))
    # print('build_keywords_list_spacy: Resquesting query string, only keywords: {}\n'.format(keywords_concat))

    return keywords_concat
 

def french_singular_to_plural(word):
    word_plural = ''

    if(len(word)>2):
        last2characters = word[-2:]
        last3characters = word[-3:]
        if((last2characters == 'eu') or (last2characters == 'au') or (last2characters == 'ou')):
            word_plural = word+'x'
        elif((last2characters == 'al')):
            word_plural = (word[:-2])+'aux'
        elif((last3characters == 'ail')):
            word_plural = (word[:-3])+'aux'
        else:
            word_plural = word+'s'
    else:
        word_plural = word
    
    return word_plural



def french_plural_to_singular(word):
    word_singular = ''

    if(len(word)>2):
        word_singular = word[:-1]
    
    return word_singular


# check if url can be accessible
def check_url(url):
    url_accessibility = False

    url = ''

    request = requests.get(url)
    # # request = requests.get(url)
    print('functions::check_url: requests.get({})'.format(url))
    # # print(request.json())

    # print('functions::check_url: request.status_code = {}'.format(request.status_code))

    if request.status_code == 200:
        print('functions::check_url: l\'url {} est accessible!'.format(url))
        url_accessibility = True
    else:
        print('functions::check_url: l\'url {} n\'est pas accessible!'.format(url)) 



    # h = httplib2.Http()
    # resp = h.request(url, 'HEAD')
    # assert int(resp[0]['status']) < 400

    # if int(resp[0]['status']) < 400:
    #     print('functions::check_url: l\'url {} est accessible!'.format(url))
    #     url_accessibility = True
    # else:
    #     print('functions::check_url: l\'url {} n\'est pas accessible!'.format(url)) 



    # fp = urllib.request.urlopen(url)
    # mybytes = fp.read()

    # mystr = mybytes.decode("utf8")
    # fp.close()

    # print(mystr)


    # from urllib.request import urlopen
    # html = urlopen(url).read()
    # print(html)

    return url_accessibility