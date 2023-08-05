'''合併消融研究'''
import os
import re
import csv

part_list = ['part1', 'part2', 'part4', 'part5', 'part6', 'part7']

with open(os.path.join('run/NkustMTMC', f'ablation-studies5.csv'), 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['part', 'studies', 'IDF1', 'IDR', 'IDP'])
    for part in part_list:
        root_path = os.path.join('run/NkustMTMC', part)
        # cvs_files = ['original-eval.csv', 'complete-eval.csv', 'aspectRatio-eval.csv', 'cosineDistance-eval.csv']
        # cvs_files = ['original-eval.csv', 'complete-eval.csv', 'feature_count-eval.csv', 'cosineDistance-eval.csv']
        # cvs_files = ['add-non-eval.csv', 'add-t1-eval.csv', 'feature_count-eval.csv', 'original-eval.csv']
        # cvs_files = ['add-non-eval.csv', 'add-t3-eval.csv', 'add-t3-t5-eval.csv', 'original-eval.csv']
        cvs_files = ['add-non-collate-eval.csv', 'add-t3-collate-eval.csv', 'add-t3-t5-collate-eval.csv', 'original-collate-eval.csv']
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
