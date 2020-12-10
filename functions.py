# -*- coding: utf-8 -*-

import spacy
import urllib
import re
import math
from gensim.corpora import Dictionary
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import random as rd
import codecs
import nltk.data
from multiprocessing import Process, Lock
import copy

nlp = spacy.load("pt_core_news_sm")
rd.seed(4321)

def read_xml(xml_file_location, abbreviations=None):
    tokenizer = nltk.data.load('tokenizers/punkt/portuguese.pickle')
    tree = ET.parse(xml_file_location)
    root = tree.getroot()
    soup = None
    docs = []
    if abbreviations != None:
        for item in abbreviations:
            tokenizer._params.abbrev_types.add(item)

    for paragraph in root.iter('Texto'):
        #print(paragraph.text)
        soup = BeautifulSoup(paragraph.text, 'html.parser')
        for p in soup.select('p'):
            texto = p.text.replace('\r', ' ').replace('\n', ' ').strip()
            if len(texto) > 0:
                doc = tokenizer.tokenize(texto.lower())
                docs.extend(doc)
    return docs

def read_html(file_location, abbreviations=None):
    tokenizer = nltk.data.load('tokenizers/punkt/portuguese.pickle')
    docs = []
    if abbreviations != None:
        for item in abbreviations:
            tokenizer._params.abbrev_types.add(item)

    with codecs.open(file_location, 'r', 'utf-8') as f:
        content = f.read()
        soup = BeautifulSoup(content, features = 'lxml')
        paragraphs = soup.find_all('p')
        for p in paragraphs:
            texto = p.text.replace("\r", '').replace("\n", ' ').strip().lower()
            if len(texto) > 0:
                doc = tokenizer.tokenize(texto)
                docs.extend(doc)
    return docs

def tokenizer_sentence(text, spacy_model=None, lemm_alternatives=None, exeption_lst=['ADJ', 'PROPN', 'NOUN'], insert_val_mask=True, debug=False):
    last_viewed = None
    text_split = re.split(r'(\W+)', text)
    #text_split = re.sub(r'\W+', ' ', text)
    if spacy_model == None:
        nlp = spacy.load("pt_core_news_sm")
    else:
        nlp = spacy_model
        
    model = nlp(' '.join(text_split).strip())
    #model = nlp(text_split.strip())
    tokens = []
    new_tokens = []
    count = 0
    for word in model:
        str_word = str(word.text).lower().strip()
        if str_word != last_viewed:
            if count > 0:
                tokens += new_tokens + ['##SEQT']
            elif last_viewed != None:
                tokens += new_tokens
                
            new_tokens = []
            last_viewed = str_word
            count = 0
            
            num = True
            len_word = 0
            
            if lemm_alternatives and str_word in lemm_alternatives:
                    str_lemma = lemm_alternatives[str_word].lower()
            else:
                str_lemma = str(word.lemma_).lower().strip()
                
            try:
                int(str_word)
            except:
                num = False

            if num:
                new_tokens.append('##NUM')
                if insert_val_mask:
                    new_tokens.append(str_word)
                if debug:
                    print(str_word)
                    print(f'num: {word.pos_}')
            elif word.pos_ == 'NUM':
                new_tokens.append('##NUMEXT')
                if insert_val_mask:
                    new_tokens.append(str_word)
                if debug:
                    print(str_word)
                    print(f'num: {word.pos_}')
            elif word.pos_ in exeption_lst:
                if debug:
                    print(str_word)
                    print(f'in exeption list: {word.pos_}')
                tokens.append(str_word)
            elif len(str_word) > 0 and str_word == str_lemma:
                new_tokens.append(str_word)
            else:
                #lemma
                i = 0
                
                if len(str_lemma) < len(str_word):
                    len_word = len(str_lemma)
                else:
                    len_word = len(str_word)

                while i < len_word and str_word[i] == str_lemma[i]:
                    i += 1
                #print(str_word, str_lemma)
                if i == 0 and len(str_word) > 0:
                    new_tokens.append(str_word)              
                    new_tokens.append('##' + str_lemma)
                elif len(str_word[:i].strip()) > 0:
                    new_tokens.append(str_word[:i].strip())

                if i != 0 and len(str_word[i:].strip()) > 0:
                    new_tokens.append('##' + str_word[i:].strip())

                if debug:
                    print(i)
                    print(str_word)
                    print(str_lemma[0:i], str_lemma[i:])
                    print(word.pos_)
        else:
            count += 1
                
    return tokens + new_tokens

# Lock at the dictionary and make a deep copy
def pack_tokens(tokens, dictionary, lock, max_length = 512):
    nr_sep = math.ceil(len(tokens)/max_length)
    max_length_sep = max_length - nr_sep
    blks = math.ceil(len(tokens)/max_length_sep)
    blocks = []
    dict_copy = None
    
    lock.acquire()
    try:
        dictionary.add_documents([tokens])
        dict_copy = copy.deepcopy(dictionary)
    finally:
        lock.release()

    dict_in = []
    dict_out = []
    for i in range(blks):
        size_res = 0
        mask = [1] * max_length
        offset = max_length_sep*i
        #print(len(tokens[offset:(max_length_sep + offset)]))
        res = ["[CLS]"] + tokens[offset:(max_length_sep + offset)] + ["[SEP]"]
        size_res = len(res)
        if size_res < max_length:
            for i in range(size_res, max_length):
                mask[i] = 0
                res.append('[PAD]')
        #print(len(res))
        pos_mask, data_mask = mask_block(res, dict_copy)
        for it in data_mask:
            dict_in.append(dict_copy.token2id[it])
            
        for it in res:
            dict_out.append(dict_copy.token2id[it])
            
        blocks.append((size_res, pos_mask, data_mask, res, dict_in, dict_out, mask))
    return blocks

def mask_block(block, dictionary=None):
    prob = rd.random()
    if prob <= 0.1:
        return -1, block
    else:
        mask_pos = rd.randint(1, block.index("[SEP]"))
        #print(mask_pos)
        if block[mask_pos] not in ["[CLS]", "[SEP]", "[PAD]"]:
            if prob <= 0.2:
                if dictionary == None:
                    mask_pos2 = rd.randint(1, block.index("[SEP]")-1)
                    if mask_pos2 != mask_pos:
                        return mask_pos, block[0:mask_pos] + block[mask_pos2] + block[mask_pos+1:]
                    else:
                        return mask_pos, block[0:mask_pos] + block[mask_pos2+1] + block[mask_pos+1:]
                else:
                    mask_pos2 = rd.randint(4, len(dictionary)-1)
                    if dictionary.token2id[block[mask_pos]] != mask_pos2:
                        return mask_pos, block[0:mask_pos] + [dictionary[mask_pos2]] + block[mask_pos+1:]
                    else:
                        return mask_pos, block[0:mask_pos] + [dictionary[mask_pos2+1]] + block[mask_pos+1:]
            else:
                return mask_pos, block[0:mask_pos] + ['[MASK]'] + block[mask_pos+1:]
    return mask_pos, block