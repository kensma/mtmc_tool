'''將同一軌跡中間缺失幀補齊'''
import numpy as np
import yaml
import os
import csv
from collections import defaultdict
import sys

def interpolation(cam_infos, target_path, save_path="interpolation", max_missing_frames=60):
    if not os.path.exists(save_path):
        os.makedirs(save_path)

    for cam_info in cam_infos:
        csv_file_name = f'{cam_info["name"]}_target.csv'
        target_csv_path = os.path.join(target_path, csv_file_name)

        frame_rows = defaultdict(list)
        targets = {}

        with open(target_csv_path, newline='') as csvfile:
                spamreader = csv.reader(csvfile)
                for row in list(spamreader):
                    frame_id, *xyxy, conf, cls, track_id, match_id, match_conf = row
                    frame_id = int(frame_id)
                    frame_rows[frame_id].append(row)

                    if match_id in targets and frame_id - int(targets[match_id][0]) > 1:
                        prev_row = targets[match_id]
                        prev_frame_id = int(prev_row[0])
                        prev_xyxy = prev_row[1:5]
                        prev_xyxy = np.array([float(x) for x in prev_xyxy])
                        if np.min(prev_xyxy) < 0 or np.max(prev_xyxy) > 1920:
                            continue

                        missing_frames = frame_id - prev_frame_id - 1
                        # 最大補齊幀數
                        if missing_frames > max_missing_frames:
                            continue
                        linspace = np.linspace(prev_xyxy, np.array([float(x) for x in xyxy]), missing_frames)
                        for i, xyxy in enumerate(linspace[1:-1]):
                            frame_rows[prev_frame_id + i + 1].append([prev_frame_id + i + 1, *linspace[i], *prev_row[5:]])

                    targets[match_id] = row

        with open(os.path.join(save_path, csv_file_name), 'a', newline='') as csvfile:
            csv_writer = csv.writer(csvfile)
            for frame_id in sorted(list(frame_rows.keys())):
                for row in frame_rows[frame_id]:
                    csv_writer.writerow(row)

if __name__ == '__main__':
    cfg_name = sys.argv[1] if len(sys.argv) > 1 else 'nd_v2_p1.yaml'
    cfg_path = os.path.join('cfg', cfg_name)

    config = yaml.load(open(cfg_path, 'r'), Loader=yaml.FullLoader)

    cam_infos = config['cam_infos']
    run_path = config['run_path']
    save_path = os.path.join(run_path, 'interpolation')
    target_path = os.path.join(run_path, config['target_path'])