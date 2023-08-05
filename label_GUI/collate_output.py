'''將原始輸出整理'''
from collections import defaultdict
# from utils.plots import plot_one_box
import csv
import yaml
import os
import sys

# cfg_name = sys.argv[1] if len(sys.argv) > 1 else 'nd_v2_p1.yaml'
# cfg_path = os.path.join('cfg', cfg_name)
# config = yaml.load(open(cfg_path, 'r'), Loader=yaml.FullLoader)

# cam_infos = config['cam_infos']
# run_path = config['run_path']
# tracker_folders = ['add-non', 'add-t3', 'add-t3-t5', 'original']


def collate(cam_infos, target_path, save_path="collate"):

    if not os.path.exists(save_path):
        os.makedirs(save_path)

    match_ids = set()
    for cam_info in cam_infos:
        csv_file_name = f'{cam_info["name"]}_target.csv'
        target_csv_path = os.path.join(target_path, csv_file_name)
        frame_targets = defaultdict(list)
        tracks = {}
        with open(target_csv_path, newline='') as csvfile:
                spamreader = csv.reader(csvfile)
                for row in reversed(list(spamreader)):
                    frame_id, *xyxy, conf, cls, track_id, match_id, match_conf = row
                    if track_id not in tracks:
                        if match_id != '':
                            tracks[track_id] = match_id
                            match_ids.add(int(match_id))
                        else:
                            match_id = max(match_ids) + 1
                            match_ids.add(match_id)
                            tracks[track_id] = str(match_id)

                    frame_targets[int(frame_id)].append((*xyxy, conf, cls, tracks[track_id], tracks[track_id]))

        # for k, v in tracks.items():
        #     if v == '':
        #         match_id = max(match_ids) + 1
        #         match_ids.add(match_id)
        #         tracks[k] = str(match_id)

        with open(os.path.join(save_path, csv_file_name), 'a', newline='') as csvfile:
            csv_writer = csv.writer(csvfile)
            for frame_id in sorted(list(frame_targets.keys())):
                for target in frame_targets[frame_id]:
                    csv_writer.writerow([frame_id, *target, ''])

if __name__ == '__main__':
    cfg_name = sys.argv[1] if len(sys.argv) > 1 else 'nd_v2_p1.yaml'
    cfg_path = os.path.join('cfg', cfg_name)
    config = yaml.load(open(cfg_path, 'r'), Loader=yaml.FullLoader)

    cam_infos = config['cam_infos']
    run_path = config['run_path']
    save_path = os.path.join(run_path, "collate")
    target_path = os.path.join(run_path, config['target_path'])

    collate(cam_infos, target_path, save_path)