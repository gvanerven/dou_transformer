#http://thiagomarzagao.com/2020/07/08/diario-embeddings/
import os
import requests
from bs4 import BeautifulSoup

months = [
    # month names in Portuguese
    'janeiro',
    'fevereiro',
    'marco',
    'abril',
    'maio',
    'junho',
    'julho',
    'agosto',
    'setembro',
    'outubro',
    'novembro',
    'dezembro'
]

# path to the folder that will store the zip files
basepath = '/mnt/d/DOU/arquivos/' # create the folder first

# loop through years and months
for year in range(2002, 2021): # change end year if you're in the future
    for month in months:
        print(year, month)
        url = 'http://www.in.gov.br/dados-abertos/base-de-dados/publicacoes-do-dou/{}/{}'.format(str(year), month)
        r = requests.get(url)
        soup = BeautifulSoup(r.content)
        tags = soup.find_all('a', class_ = 'link-arquivo')
        urls = ['http://www.in.gov.br' + e['href'] for e in tags]
        fnames = [e.text for e in tags]
        for url, fname in zip(urls, fnames):
            if not os.path.isfile(basepath + fname):
                try:
                    r = requests.get(url)
                    with open(basepath + fname, mode = 'wb') as f:
                        f.write(r.content)
                except:
                    continue
