# -*- coding: utf-8 -*-

from gensim.corpora import Dictionary
import os
import argparse
import functions
import codecs
import sys
from multiprocessing import Process, Lock
import math


def process_list(walk_list, lock, num, dictionary, destination_dir='.', lemm_alternatives=None, abbreviations=None):
    nr_processed = 0
    for (idx_doc, filename, filepath) in walk_list:
        print(f'Processing {filepath} by job {num}')
        try:
            docs = functions.read_xml(filepath, abbreviations=abbreviations)
            #print(docs)
            file_save = os.path.join(destination_dir, filename.replace(".xml", ".dat"))
            with codecs.open(file_save, 'w', 'utf-8') as fs:
                for idx_sent, doc in enumerate(docs):
                    packs = functions.pack_tokens(functions.tokenizer_sentence(doc, lemm_alternatives=lemm_alternatives, insert_val_mask=False), dictionary, lock, max_length=128)
                    for idx_block, tp in enumerate(packs):
                        fs.write(f'#[{idx_doc}, {idx_sent}, {idx_block}, {tp[0]}, {tp[1]}]' + "\n")
                        for i in range(2, len(tp)):
                            fs.write('##' + str(tp[i]) + "\n")
            nr_processed += 1
        except Exception as e:
            err = sys.exc_info()[0]
            print(f"Error processing {filepath} in job {num}: {err} -> {e}")
    print(f'Nr docs processed: {nr_processed}')
    return nr_processed

def break_file_list(file_list, n_jobs):
    lsts = []
    len_jobs = n_jobs if len(file_list) >= n_jobs else len(file_list)
    for i in range(len_jobs):
        lsts.append([])

    for i, item in enumerate(file_list):
        lsts[i % len_jobs].append(item)
    
    for lst in lsts:
        yield lst

if __name__ == '__main__':
    lock = Lock()
    parser = argparse.ArgumentParser(description='Pre-processing XML DOU')
    parser.add_argument('--data_dir', type=str, default='./arquivos_xml', help='location of the data files')
    parser.add_argument('--data_out', type=str, default='./arquivos_dat', help='destination of the processed files')
    parser.add_argument('--n_jobs', type=int, default=5, help='number of processes')
    args = parser.parse_args()

    dataset = []
    dictionary = Dictionary()
    dictionary.add_documents([["[CLS]"], ["[SEP]"], ["[MASK]"], ["[PAD]"]])
    lemm_alt = {"para": "para",
                "defesa": "defesa",
                "a": "a",
                "as": "a",
                "na": "a"}

    abbreviations = ['art']
    destination_dir = args.data_out
    n_jobs = args.n_jobs

    list_files = []
    idx_doc = 0
    for (dirpath, dirnames, filenames) in os.walk(args.data_dir):
        for file in filenames:
            if file[-4:] == '.xml':
                filepath = os.path.join(dirpath, file)
                list_files.append((idx_doc, file, filepath))
                idx_doc += 1

    jobs = []
    for num, partition in enumerate(break_file_list(list_files, n_jobs)):
        print(f"Partition's size {len(partition)}")
        p = Process(target=process_list, args=(partition, lock, num, dictionary, destination_dir, lemm_alt, abbreviations))
        jobs.append(p)
        p.start()

    for job in jobs:
        job.join()

    dictionary.save('dictionary.sav')
