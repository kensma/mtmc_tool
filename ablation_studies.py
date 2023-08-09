'''合併消融研究'''
import os
import re
import csv

part_list = ['part0', 'part1', 'part2']

with open(os.path.join('run/ConvenienceStoreMTMC', f'ablation-studies.csv'), 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['part', 'studies', 'IDF1', 'IDR', 'IDP'])
    for part in part_list:
        root_path = os.path.join('run/ConvenienceStoreMTMC', part)
        cvs_files = ['add-non-eval.csv', 'add-t3-eval.csv', 'add-t3-t5-eval.csv', 'original-eval.csv']
        for i, cvs_file in enumerate(cvs_files):
            with open(os.path.join(root_path, cvs_file), 'r') as f:
                lines = f.readlines()
                lines = list(filter(lambda x: x.startswith('global'), lines))
                for line in lines:
                    line = line.strip()
                    line = re.sub(r' +', ' ', line)
                    line = line.split(',')
                    part_name = part if i == 0 else ''
                    writer.writerow([part_name, cvs_file[:-9], line[1], line[3], line[2]])
