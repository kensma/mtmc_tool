'''將bbox的位置資訊平滑化'''
import numpy as np
import yaml
import os
import csv
from scipy.signal import savgol_filter
import sys

class Target:
    def __init__(self, match_id, frame_id, xyxy, cls):
        self.match_id = match_id
        self.min_frame_id = frame_id
        self.max_frame_id = frame_id
        self.xyxy = {}
        self.cls = cls
        self.add(frame_id, xyxy)

    def add(self, frame_id, xyxy):
        self.max_frame_id = frame_id
        self.xyxy[frame_id] = np.array([float(x) for x in xyxy])

    def get(self, frame_id):
        return [frame_id, *self.xyxy[frame_id], '', self.cls, self.match_id, self.match_id, '']

    def smooth(self):
        values = []
        keys = sorted(list(self.xyxy.keys()))
        for key in keys:
            values.append(self.xyxy[key])
        values = np.array(values)

        if len(values) >= 5:
            savgol_values = savgol_filter(values, 5, 3, axis=0)

            for i, key in enumerate(keys):
                self.xyxy[key] = savgol_values[i]

    def __lt__(self, other):
        return self.min_frame_id < other
    def __gt__(self, other):
        return self.max_frame_id > other
    def __le__(self, other):
        return self.max_frame_id <= other
    def __ge__(self, other):
        return self.max_frame_id >= other

def smooth(cam_infos, target_path, save_path="smooth"):
    if not os.path.exists(save_path):
        os.makedirs(save_path)

    for cam_info in cam_infos:
        csv_file_name = f'{cam_info["name"]}_target.csv'
        target_csv_path = os.path.join(target_path, csv_file_name)

        frame_set = set()
        Targets = {}

        with open(target_csv_path, newline='') as csvfile:
                spamreader = csv.reader(csvfile)
                for row in list(spamreader):
                    frame_id, *xyxy, conf, cls, track_id, match_id, match_conf = row
                    frame_id = int(frame_id)
                    frame_set.add(frame_id)

                    if match_id in Targets:
                        Targets[match_id].add(frame_id, xyxy)
                    else:
                        Targets[match_id] = Target(match_id, frame_id, xyxy, cls)
        
        for target in Targets.values():
            target.smooth()

        with open(os.path.join(save_path, csv_file_name), 'a', newline='') as csvfile:
            csv_writer = csv.writer(csvfile)
            for frame_id in sorted(frame_set):
                for target in Targets.values():
                    if frame_id in target.xyxy:
                        csv_writer.writerow(target.get(frame_id))

if __name__ == '__main__':
    cfg_name = sys.argv[1] if len(sys.argv) > 1 else 'nd_v2_p1.yaml'
    cfg_path = os.path.join('cfg', cfg_name)

    config = yaml.load(open(cfg_path, 'r'), Loader=yaml.FullLoader)

    cam_infos = config['cam_infos']
    run_path = config['run_path']
    save_path = os.path.join(run_path, "smooth")
    target_path = os.path.join(run_path, config['target_path'])

    smooth(cam_infos, target_path, cfg_path)
