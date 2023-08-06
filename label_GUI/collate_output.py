'''將原始輸出整理'''
from collections import defaultdict
# from utils.plots import plot_one_box
import csv
import yaml
import os
import sys

class SerialNumber:
    def __init__(self):
        self.count = 0
    def __call__(self):
        count = self.count
        self.count += 1
        return count
    def reset(self):
        self.count = 0

def collate(cam_infos, target_path, save_path="collate"):

    if not os.path.exists(save_path):
        os.makedirs(save_path)

    serial_number = SerialNumber()
    number = defaultdict(serial_number)
    match_ids = set()
    multi_frame_targets = {}
    max_frame = 0
    for cam_info in cam_infos:
        csv_file_name = f'{cam_info["name"]}_target.csv'
        target_csv_path = os.path.join(target_path, csv_file_name)
        frame_targets = defaultdict(list)
        tracks = {}
        with open(target_csv_path, newline='') as csvfile:
                spamreader = csv.reader(csvfile)
                for row in reversed(list(spamreader)):
                    frame_id, *xyxy, conf, cls, track_id, match_id, match_conf = row
                    max_frame = max(max_frame, int(frame_id))
                    if track_id not in tracks:
                        if match_id != '':
                            match_id = int(match_id)
                            if match_id in match_ids:
                                match_id = max(match_ids) + 1
                                while match_id in match_ids:
                                    match_id += 1
                            tracks[track_id] = match_id
                            match_ids.add(match_id)
                        else:
                            match_id = max(match_ids) + 1
                            while match_id in match_ids:
                                    match_id += 1
                            match_ids.add(match_id)
                            tracks[track_id] = match_id
                    if track_id in tracks and match_id != '' and tracks[track_id] != int(match_id):
                        tracks[track_id] = int(match_id)

                    frame_targets[int(frame_id)].append((*xyxy, conf, cls, tracks[track_id], tracks[track_id]))
                multi_frame_targets[cam_info["name"]] = frame_targets

    csvs = {}
    for cam_info in cam_infos:
        csv_file_name = f'{cam_info["name"]}_target.csv'
        csv_file = open(os.path.join(save_path, csv_file_name), 'a', newline='')
        csv_writer = csv.writer(csv_file)
        csvs[cam_info["name"]] = {'file': csv_file, 'writer': csv_writer}

    for frame_id in range(max_frame):
        for cam_info in cam_infos:
            cam_name = cam_info["name"]
            for target in multi_frame_targets[cam_name][frame_id]:
                *xyxy, conf, cls, track_id, match_id = target
                csvs[cam_name]['writer'].writerow([frame_id, *xyxy, conf, cls, str(number[track_id]), str(number[match_id]), ''])

    for cam_info in cam_infos:
        csvs[cam_info["name"]]['file'].close()

if __name__ == '__main__':
    cfg_name = sys.argv[1] if len(sys.argv) > 1 else 'nd_v2_p1.yaml'
    cfg_path = os.path.join('cfg', cfg_name)
    config = yaml.load(open(cfg_path, 'r'), Loader=yaml.FullLoader)

    cam_infos = config['cam_infos']
    run_path = config['run_path']
    save_path = os.path.join(run_path, "collate")
    target_path = os.path.join(run_path, config['target_path'])

    collate(cam_infos, target_path, save_path)