'''視覺化&儲存'''
from collections import defaultdict
# from utils.plots import plot_one_box
import argparse
import random
import csv
import cv2
import math
import math
import numpy as np
import yaml
import os
import sys

def plot_one_box(x, img, color=None, label=None, line_thickness=3):
    # Plots one bounding box on image img
    tl = line_thickness or round(0.002 * (img.shape[0] + img.shape[1]) / 2) + 1  # line/font thickness
    color = color or [random.randint(0, 255) for _ in range(3)]
    c1, c2 = (int(x[0]), int(x[1])), (int(x[2]), int(x[3]))
    cv2.rectangle(img, c1, c2, color, thickness=tl, lineType=cv2.LINE_AA)
    if label:
        tf = max(tl - 1, 1)  # font thickness
        t_size = cv2.getTextSize(label, 0, fontScale=tl / 3, thickness=tf)[0]
        c2 = c1[0] + t_size[0], c1[1] - t_size[1] - 3
        cv2.rectangle(img, c1, c2, color, -1, cv2.LINE_AA)  # filled
        cv2.putText(img, label, (c1[0], c1[1] - 2), 0, tl / 3, [225, 255, 255], thickness=tf, lineType=cv2.LINE_AA)

class PlotVideo:
    def __init__(self, cam_info, target_path, save_bbox_img=False, save_bbox_img_path=None):
        self.cam_name = cam_info['name']
        self.video_path = cam_info['file']
        self.target_csv_path = os.path.join(target_path, f'{self.cam_name}_target.csv')

        self.save_bbox_img = save_bbox_img
        self.save_bbox_img_path = save_bbox_img_path

        self.frame_targets = defaultdict(list)
        self.frame_id = 0
        with open(self.target_csv_path, newline='') as csvfile:
            spamreader = csv.reader(csvfile)
            for row in spamreader:
                frame_id, *xyxy, conf, cls, track_id, match_id, match_conf = row
                frame_id = int(frame_id)
                xyxy = tuple([float(x) for x in xyxy])
                conf = float(conf) if conf != '' else 1.0
                cls = int(float(cls))
                track_id = int(track_id)
                if match_id == '':
                    match_id = None
                else:
                    match_id = int(match_id)
                if match_conf == '':
                    match_conf = None
                else:
                    match_conf = float(match_conf)

                self.frame_targets[frame_id].append((xyxy, conf, cls, track_id, match_id, match_conf))

        self.cap = cv2.VideoCapture(self.video_path)

    def get_plot_frame(self, frame_id = None):
        if frame_id is not None:
            self.frame_id = frame_id
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.frame_id)
        ret, frame = self.cap.read()
        if not ret:
            return None
        
        if self.save_bbox_img:
            for xyxy, conf, cls, track_id, match_id, match_conf in self.frame_targets[self.frame_id]:
                save_path = os.path.join(self.save_bbox_img_path, self.cam_name)
                if not os.path.exists(save_path):
                    os.makedirs(save_path)
                in_border = np.min(xyxy) < 0
                in_border = frame.shape[0] < xyxy[3] or frame.shape[1] < xyxy[2] or in_border
                xyxy = list(map(lambda x: 0 if x < 0 else x, xyxy ))
                file_name = f'{self.frame_id}_{track_id}'
                file_name += '_in_border' if in_border else ''
                file_name += '.jpg'
                cv2.imwrite(os.path.join(save_path, file_name), frame[int(xyxy[1]):int(xyxy[3]), int(xyxy[0]):int(xyxy[2])])

        for xyxy, conf, cls, track_id, match_id, match_conf in self.frame_targets[self.frame_id]:
            label = f'{names[int(cls)]}  {int(track_id)}  {conf:.2f}'
            color = [226,228,229]
            if isinstance(match_id, int):
                label += f' #{match_id}'
                color = colors[int(match_id)]
                if isinstance(match_conf, float):
                    label += f' {match_conf:.4f}'

            plot_one_box(xyxy, frame, label=label, color=color, line_thickness=3)
        self.frame_id += 1
        return frame


if __name__ == '__main__':
    cfg_name = sys.argv[1] if len(sys.argv) > 1 else 'supermarket_p0.yaml'
    cfg_path = os.path.join('cfg', cfg_name)
    config = yaml.load(open(cfg_path, 'r'), Loader=yaml.FullLoader)

    max_frame_id = config['max_frame_id']
    cam_infos = config['cam_infos']
    run_path = config['run_path']

    if config['save_video']:
        fourcc = cv2.VideoWriter_fourcc(*'MP4V')
        out = cv2.VideoWriter(os.path.join(run_path, config['save_video_name']), fourcc, float(config['save_video_fps']), config['save_video_size'])

    global names, colors
    with open("classes.txt", newline='') as f:
        names = f.read().split('\n')
    random.seed(10)
    colors = defaultdict(lambda :[random.randint(0, 255) for _ in range(3)])

    size = math.ceil(len(cam_infos) ** 0.5)
    frame_id = 0
    frame_id_change = False
    count = max_frame_id

    merge_img_list = []
    PlotVideos = []

    for cam_info in cam_infos:
        PlotVideos.append(PlotVideo(cam_info, os.path.join(run_path, config['target_path']), config['save_bbox_img'], os.path.join(config['save_bbox_img_path'], config['save_video_name'])))
        merge_img_list.append(None)

    while frame_id < max_frame_id:
        if count > 0:
            for i, PlotVideo in enumerate(PlotVideos):
                if frame_id_change:
                    frame = PlotVideo.get_plot_frame(frame_id)
                else:
                    frame = PlotVideo.get_plot_frame()
                frame = frame if frame is not None else merge_img_list[i]
                cv2.putText(frame, cam_infos[i]['name'], (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 112, 0), 3, cv2.LINE_AA)
                merge_img_list[i] = frame
            frame_id_change = False

            merge_img = []
            for r in range(size):
                if r*size+1 > len(merge_img_list):
                    break
                c_img = merge_img_list[r*size]
                shape = c_img.shape
                for c in range(size-1):
                    index = (r*size)+(c+1)
                    if index >= len(merge_img_list):
                        c_img = np.concatenate((c_img, np.zeros(shape, dtype=np.uint8)), axis=1)
                        break
                    c_img = np.concatenate((c_img, merge_img_list[index]), axis=1)
                merge_img.append(c_img)
            merge_img = np.concatenate(merge_img, axis=0)
            merge_img = cv2.resize(merge_img, (1920, 1080))
            cv2.putText(merge_img, str(frame_id), (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 112, 0), 3, cv2.LINE_AA)

            frame_id += 1
            count -= 1

        if config['save_video']:
            out.write(merge_img)
        cv2.imshow('merge_img', merge_img)
        key = cv2.waitKey(1)

        if key == ord('q'):
            break
        elif key == ord('0'):
            frame_id = 0
            frame_id_change = True
            count = max_frame_id
        elif key == ord('d'):
            frame_id -= 2
            frame_id = max(frame_id, 0)
            frame_id_change = True
            count = 1
        elif key == ord('4'):
            frame_id -= 30
            frame_id = max(frame_id, 0)
            frame_id_change = True
            count = 1
        elif key == ord('f'):
            # frame_id += 1
            frame_id = min(frame_id, max_frame_id)
            frame_id_change = True
            count = 1
        elif key == ord('6'):
            frame_id += 30
            frame_id = min(frame_id, max_frame_id)
            frame_id_change = True
            count = 1
        elif key == ord(' '):
            if count > 0:
                count = 0
            else:
                count = max_frame_id - (frame_id+1)

    if config['save_video']:
        out.release()
