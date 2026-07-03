# -*- coding: utf-8 -*-
import zipfile
import csv

def test():
    zip_path = r"C:\Users\china\Desktop\出货资料检验\加拿大 工厂发货 漳州元邦 295宽50厚隐形人造板层板(CA站) 7-10 货好 大件 FBA19H301DVS 货代自建仓.zip"
    with zipfile.ZipFile(zip_path, 'r') as z:
        csv_name = [f for f in z.namelist() if f.endswith('.csv')][0]
        content = z.read(csv_name).decode('gbk', errors='ignore')
        print("GBK Decode Head:")
        lines = content.splitlines()
        for l in lines[:12]:
            if l:
                print(list(csv.reader([l]))[0])

if __name__ == '__main__':
    test()
