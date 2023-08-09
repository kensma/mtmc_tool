'''評估指標'''
import os
import sys
import yaml
import csv

from utils import get_preprocessed_data, calculate_box_ious
from trackeval.metrics.identity import Identity
from trackeval.metrics.identity_mtmc import IdentityMTMC

identity = Identity({
    'PRINT_CONFIG': False,  # Whether to print the config information on init. Default: False.
})
identity_mtmc = IdentityMTMC({
        'PRINT_CONFIG': False,  # Whether to print the config information on init. Default: False.
})

cfg_name = sys.argv[1] if len(sys.argv) > 1 else 'convenienceStoreMTMC_p1.yaml'
cfg_path = os.path.join('cfg', cfg_name)
config = yaml.load(open(cfg_path, 'r'), Loader=yaml.FullLoader)

run_path = config['run_path']
max_frame = config['max_frame_id']

cam_infos = config['cam_infos']
cams = [cam_info['name'] for cam_info in cam_infos]

gt_path = config['gt_path']
# tracker_path = os.path.join(run_path, 'original')
tracker_folders = ['add-non', 'add-t3', 'add-t3-t5', 'original']
# tracker_folders = ['original']

for tracker_folder in tracker_folders:
    tracker_path = os.path.join(run_path, tracker_folder)

    results = {}

    for cam in cams:
        num_gt_ids, gt_ids, num_gt_dets, gt_dets = get_preprocessed_data(gt_path, [cam], max_frame, file_format='{}.csv')
        num_tracker_ids, tracker_ids,  num_tracker_dets, tracker_dets = get_preprocessed_data(tracker_path, [cam], max_frame)

        similarity_scores = [None for i in range(max_frame)]
        for t, (gt_dets_t, tracker_dets_t) in enumerate(zip(gt_dets, tracker_dets)):
            ious = calculate_box_ious(gt_dets_t, tracker_dets_t, box_format='x0y0x1y1')
            similarity_scores[t] = ious

        data = {
        'num_timesteps' : max_frame,
        'num_gt_ids' : num_gt_ids,
        'num_tracker_ids' : num_tracker_ids,
        'num_gt_dets' : num_gt_dets,
        'num_tracker_dets' : num_tracker_dets,
        'gt_ids' : gt_ids,
        'tracker_ids' : tracker_ids,
        'similarity_scores' : similarity_scores,
        }

        res = identity.eval_sequence(data)
        results[cam] = res

    '''全局'''

    num_gt_ids, gt_ids, num_gt_dets, gt_dets = get_preprocessed_data(gt_path, cams, max_frame, file_format='{}.csv')
    num_tracker_ids, tracker_ids,  num_tracker_dets, tracker_dets = get_preprocessed_data(tracker_path, cams, max_frame)

    similarity_scores = {cam : [None for i in range(max_frame)] for cam in cams}
    for cam in cams:
        for t in range(max_frame):
            gt_dets_t = gt_dets[cam][t]
            tracker_dets_t = tracker_dets[cam][t]
            ious = calculate_box_ious(gt_dets_t, tracker_dets_t)
            similarity_scores[cam][t] = ious

    data = {
        'cams': cams,
        'num_timesteps' : max_frame,
        'num_gt_ids' : num_gt_ids,
        'num_tracker_ids' : num_tracker_ids,
        'num_gt_dets' : num_gt_dets,
        'num_tracker_dets' : num_tracker_dets,
        'gt_ids' : gt_ids,
        'tracker_ids' : tracker_ids,
        'similarity_scores' : similarity_scores,
    }

    res = identity_mtmc.eval_sequence(data)
    results['global'] = res

    '''输出'''
    print('tracker_path: ', tracker_path)
    with open(os.path.join(run_path, f'{tracker_folder}-eval.csv'), 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['area', 'IDF1', 'IDP', 'IDR', 'IDTP', 'IDFN', 'IDFP'])
        print('%-10s %-7s %-7s %-7s %-7s %-7s %-7s' % ('area', 'IDF1', 'IDP', 'IDR', 'IDTP', 'IDFN', 'IDFP'))
        for key, value in results.items():
            IDF1, IDP, IDR, IDTP, IDFN, IDFP = value['IDF1'], value['IDP'], value['IDR'], value['IDTP'], value['IDFN'], value['IDFP']
            writer.writerow([key, IDF1, IDP, IDR, IDTP, IDFN, IDFP])
            print('%-10s %-7.3f %-7.3f %-7.3f %-7d %-7d %-7d' % (key, IDF1, IDP, IDR, IDTP, IDFN, IDFP))
