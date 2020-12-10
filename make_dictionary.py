# -*- coding: utf-8 -*-

from gensim.corpora import Dictionary
import argparse
import functions
from pyspark.sql import SparkSession
from pyspark import SparkConf
from pyspark import SparkContext

parser = argparse.ArgumentParser(description='Pre-processing XML DOU')
parser.add_argument('--data_dir', type=str, default='./arquivos_xml', help='location of the data files')
args = parser.parse_args()


number_cores = 5
memory_gb = 8
conf = (
    SparkConf()
        .setMaster('local[{}]'.format(number_cores))
        .set('spark.driver.memory', '{}g'.format(memory_gb))
)

spark = SparkSession.builder.appName('Word Count').getOrCreate()
sc = spark.sparkContext

sc.stop()