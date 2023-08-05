'''整理eval'''
import os
import re
import csv

part_list = ['part1', 'part2', 'part4', 'part5', 'part6', 'part7']

with open(os.path.join('run/NkustMTMC', 'total.csv'), 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['part', 'cam', 'IDF1', 'IDP', 'IDR'])
    for part in part_list:
        root_path = os.path.join('run/NkustMTMC', part)
        cvs_files = ['original-eval.csv']
        for cvs_file in cvs_files:
            with open(os.path.join(root_path, cvs_file), 'r') as f:
                lines = f.readlines()
                for i, line in enumerate(lines[1:]):
                    line = line.strip()
                    line = re.sub(r' +', ' ', line)
                    line = line.split(',')
                    part_name = part if i == 0 else ''
                    writer.writerow([part_name, line[0], line[1], line[2], line[3]])
                    # print([part_name, cvs_file[:-9], line[1], line[2], line[3]])
