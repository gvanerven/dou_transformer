#http://thiagomarzagao.com/2020/07/08/diario-embeddings/

import os
import zipfile

ipath = os.path.join('D:\\', 'DOU', 'arquivos')
opath = os.path.join('D:\\', 'DOU', 'arquivos_xml') # create folder first
for fname in os.listdir(ipath):
    if '.zip' in fname:
        year = fname[5:9]
        month = fname[3:5]
        section = fname[2:3]
        print(year, month, section, fname)
        destination = os.path.join(opath, year, month, section)
        os.makedirs(destination)
        try:
            with zipfile.ZipFile(os.path.join(ipath, fname)) as zip_ref:
                    zip_ref.extractall(destination)
        except:
            print('error; moving on') # some zip files are corrupted
