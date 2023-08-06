'''視覺化&儲存'''
from collections import defaultdict
import random
import csv
import cv2
import math
import math
import numpy as np
import os

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
    def __init__(self, cam_info, target_path):
        self.cam_name = cam_info['name']
        self.video_path = cam_info['file']
        self.target_csv_path = os.path.join(target_path, f'{self.cam_name}_target.csv')

        self.frame_targets = defaultdict(list)
        self.frame_id = 0
        self.frame = None
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
        print(f'video_path: {self.video_path}')

    def get_plot_frame(self, frame_id = None):
        if frame_id is not None:
            if frame_id == self.frame_id -1:
                return self.frame
            self.frame_id = frame_id
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.frame_id)

        ret, self.frame = self.cap.read()
        if not ret:
            return None

        for xyxy, conf, cls, track_id, match_id, match_conf in self.frame_targets[self.frame_id]:
            label = f'#{int(track_id)} {conf:.2f}'
            color = [226,228,229]
            if isinstance(match_id, int):
                label += f' | #{match_id}'
                color = colors[int(match_id)]
                if isinstance(match_conf, float):
                    label += f' {match_conf:.4f}'

            plot_one_box(xyxy, self.frame, label=label, color=color, line_thickness=3)
        self.frame_id += 1
        return self.frame
    
    def get_click_bbox(self, pos, highlight=False):
        frame_id = self.frame_id - 1
        for xyxy, conf, cls, track_id, match_id, match_conf in self.frame_targets[frame_id]:
            if xyxy[0] < pos[0] < xyxy[2] and xyxy[1] < pos[1] < xyxy[3]:
                if highlight:
                    plot_one_box(xyxy, self.frame, label="editing", color=(0,0,255), line_thickness=3)
                return int(track_id), int(match_id)
        return None, None
    
    def change_id(self, old_track_id, track_id=None, match_id=None, from_frame=None):
        for frame_id in sorted(list(self.frame_targets.keys())):
            if from_frame is not None and frame_id < from_frame:
                continue
            for i, item in enumerate(self.frame_targets[frame_id]):
                if item[3] == old_track_id:
                    t_id = track_id if track_id is not None else item[3]
                    m_id = match_id if match_id is not None else item[4]
                    self.frame_targets[frame_id][i] = (item[0], item[1], item[2], t_id, m_id, item[5])
                    break

    def save_target(self, save_path):
        csv_file_name = f'{self.cam_name}_target.csv'
        with open(os.path.join(save_path, csv_file_name), 'a', newline='') as csvfile:
            csv_writer = csv.writer(csvfile)
            for frame_id in sorted(list(self.frame_targets.keys())):
                for target in self.frame_targets[frame_id]:
                    xyxy, conf, cls, track_id, match_id, match_conf = target
                    csv_writer.writerow([frame_id, *xyxy, conf, cls, track_id, match_id, match_conf])

    def check_conflict(self, track_id=None, match_id=None, from_frame=None):
        for frame_id in sorted(list(self.frame_targets.keys())):
            if from_frame is not None and frame_id < from_frame:
                continue
            for i, item in enumerate(self.frame_targets[frame_id]):
                if track_id is not None and item[3] == track_id:
                    return True, frame_id, 'local'
                if match_id is not None and item[4] == match_id:
                    return True, frame_id, 'global'
        return False, None


class PlotVideoMulti:
    def __init__(self, config):
        self.config = config
        self.max_frame_id = config['max_frame_id']
        self.cam_infos = config['cam_infos']
        self.run_path = config['run_path']

        global names, colors
        with open("classes.txt", newline='') as f:
            names = f.read().split('\n')
        random.seed(10)
        colors = defaultdict(lambda :[random.randint(0, 255) for _ in range(3)])

        self.size = [math.ceil(len(self.cam_infos) ** 0.5)]
        self.size.append(self.size[0] - 1 if (self.size[0] ** 2) - len(self.cam_infos) >= self.size[0] else self.size[0])
        self.frame_id = 0
        self.frame_id_change = False
        self.count = self.max_frame_id

        self.merge_img_list = []
        self.PlotVideos = []

        for cam_info in self.cam_infos:
            self.PlotVideos.append(PlotVideo(cam_info, os.path.join(self.run_path, config['target_path'])))
            self.merge_img_list.append(None)
    
    def get_plot_frame(self):
        if self.frame_id < self.max_frame_id:
            if self.count > 0:
                for i, PlotVideo in enumerate(self.PlotVideos):
                    if self.frame_id_change:
                        frame = PlotVideo.get_plot_frame(self.frame_id)
                    else:
                        frame = PlotVideo.get_plot_frame()
                    frame = frame if frame is not None else self.merge_img_list[i]
                    cv2.putText(frame, self.cam_infos[i]['name'], (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 112, 0), 3, cv2.LINE_AA)
                    self.merge_img_list[i] = frame
                self.frame_id_change = False

                merge_img = []
                for r in range(self.size[1]):
                    if r*self.size[0]+1 > len(self.merge_img_list):
                        break
                    c_img = self.merge_img_list[r*self.size[0]]
                    shape = c_img.shape
                    for c in range(self.size[0]-1):
                        index = (r*self.size[0])+(c+1)
                        if index >= len(self.merge_img_list):
                            c_img = np.concatenate((c_img, np.zeros(shape, dtype=np.uint8)), axis=1)
                            break
                        c_img = np.concatenate((c_img, self.merge_img_list[index]), axis=1)
                    merge_img.append(c_img)
                merge_img = np.concatenate(merge_img, axis=0)
                merge_img = cv2.resize(merge_img, (1920, 1080))
                cv2.putText(merge_img, str(self.frame_id), (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 112, 0), 3, cv2.LINE_AA)

                self.frame_id += 1
                self.count -= 1

                return self.frame_id - 1, merge_img
            
    def get_click_bbox(self, global_pos, highlight=False):
        if self.count > 0:
            self.pauseAndStart()

        one_y = 1080 // self.size[1]
        one_x = 1920 // self.size[0]

        global_y = math.ceil(global_pos[1] / one_y)
        global_x = math.ceil(global_pos[0] / one_x)

        # 轉換成該格的座標(原本畫面大小為1280*720)
        local_y = (global_pos[1] % one_y) * (720 / one_y)
        local_x = (global_pos[0] % one_x) * (1280 / one_x)

        cam_index = (global_y-1)*self.size[0]+global_x
        if cam_index > len(self.PlotVideos):
            return None, None, None
        
        cilck_bbox_id = self.PlotVideos[cam_index-1].get_click_bbox((local_x, local_y), highlight)

        if cilck_bbox_id[0] is not None:
            self.frame_id -= 1
            self.frame_id_change = True
            self.count = 1

        return cam_index - 1, cilck_bbox_id[0], cilck_bbox_id[1]
    
    def change_id(self, cam_index, old_track_id, track_id=None, match_id=None, from_frame=None):
        self.PlotVideos[cam_index].change_id(old_track_id, track_id, match_id, from_frame)

    def check_conflict(self, cam_index, track_id=None, match_id=None, from_frame=None):
        return self.PlotVideos[cam_index].check_conflict(track_id, match_id, from_frame)

    def save_target(self, save_dir):
        save_path = os.path.join(self.run_path, save_dir)
        if not os.path.exists(save_path):
            os.makedirs(save_path)
        for PlotVideo in self.PlotVideos:
            PlotVideo.save_target(save_path)
    def to_start(self):
        self.frame_id = 0
        self.frame_id_change = True
        self.count = self.max_frame_id

    def prev_frame(self):
        self.frame_id -= 2
        self.frame_id = max(self.frame_id, 0)
        self.frame_id_change = True
        self.count = 1

    def next_frame(self):
        self.frame_id = min(self.frame_id, self.max_frame_id)
        self.frame_id_change = True
        self.count = 1

    def prev_30_frame(self):
        self.frame_id -= 30
        self.frame_id = max(self.frame_id, 0)
        self.frame_id_change = True
        self.count = 1

    def next_30_frame(self):
        self.frame_id += 30
        self.frame_id = min(self.frame_id, self.max_frame_id)
        self.frame_id_change = True
        self.count = 1

    def pauseAndStart(self):
        if self.count > 0:
            self.count = 0
        else:
            self.count = self.max_frame_id - (self.frame_id+1)

    def to_frame(self, frame_id):
        self.frame_id = frame_id
        self.frame_id_change = True
        self.count = 1
