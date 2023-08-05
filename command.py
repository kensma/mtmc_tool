import os

cfgs = ['nd_v2_p1.yaml', 'nd_v2_p2.yaml', 'nd_v2_p4.yaml', 'nd_v2_p5.yaml', 'nd_v2_p6.yaml', 'nd_v2_p7.yaml']

for cfg_name in cfgs:
    # os.popen(f'python interpolation.py {cfg_name}').read()
    # os.popen(f'python smooth.py {cfg_name}').read()
    os.popen(f'python eval.py {cfg_name}').read()
    # os.popen(f'python collate_output.py {cfg_name}').read()