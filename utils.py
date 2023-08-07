import numpy as np
from collections import defaultdict
import csv
from copy import deepcopy
import os

class SerialNumber:
    def __init__(self):
        self.count = 0
    def __call__(self):
        count = self.count
        self.count += 1
        return count
    def reset(self):
        self.count = 0

def calculate_box_ious(bboxes1, bboxes2, box_format='xywh', do_ioa=False):
    """ Calculates the IOU (intersection over union) between two arrays of boxes.
    Allows variable box formats ('xywh' and 'x0y0x1y1').
    If do_ioa (intersection over area) , then calculates the intersection over the area of boxes1 - this is commonly
    used to determine if detections are within crowd ignore region.
    """
    if box_format in 'xywh':
        # layout: (x0, y0, w, h)
        bboxes1 = deepcopy(bboxes1)
        bboxes2 = deepcopy(bboxes2)

        bboxes1[:, 2] = bboxes1[:, 0] + bboxes1[:, 2]
        bboxes1[:, 3] = bboxes1[:, 1] + bboxes1[:, 3]
        bboxes2[:, 2] = bboxes2[:, 0] + bboxes2[:, 2]
        bboxes2[:, 3] = bboxes2[:, 1] + bboxes2[:, 3]

    # layout: (x0, y0, x1, y1)
    min_ = np.minimum(bboxes1[:, np.newaxis, :], bboxes2[np.newaxis, :, :])
    max_ = np.maximum(bboxes1[:, np.newaxis, :], bboxes2[np.newaxis, :, :])
    intersection = np.maximum(min_[..., 2] - max_[..., 0], 0) * np.maximum(min_[..., 3] - max_[..., 1], 0)
    area1 = (bboxes1[..., 2] - bboxes1[..., 0]) * (bboxes1[..., 3] - bboxes1[..., 1])

    if do_ioa:
        ioas = np.zeros_like(intersection)
        valid_mask = area1 > 0 + np.finfo('float').eps
        ioas[valid_mask, :] = intersection[valid_mask, :] / area1[valid_mask][:, np.newaxis]

        return ioas
    else:
        area2 = (bboxes2[..., 2] - bboxes2[..., 0]) * (bboxes2[..., 3] - bboxes2[..., 1])
        union = area1[:, np.newaxis] + area2[np.newaxis, :] - intersection
        intersection[area1 <= 0 + np.finfo('float').eps, :] = 0
        intersection[:, area2 <= 0 + np.finfo('float').eps] = 0
        intersection[union <= 0 + np.finfo('float').eps] = 0
        union[union <= 0 + np.finfo('float').eps] = 1
        ious = intersection / union
        return ious

def get_preprocessed_data(file_path, cams, num_timesteps, file_format='{}_target.csv'):
    serial_number = SerialNumber()
    number = defaultdict(serial_number)

    num_dets = 0
    ids = {cam : [[] for i in range(num_timesteps)] for cam in cams}
    dets = {cam : [[] for i in range(num_timesteps)] for cam in cams}
    
    for cam in cams:
        with open(os.path.join(file_path, file_format.format(cam))) as f:
            spamreader = csv.reader(f)
            for row in spamreader:
                frame, *xyxy, conf, cls, track_id, match_id, match_conf = row
                frame = int(frame) - 1
                xyxy = np.array([float(x) for x in xyxy])
                match_id = int(match_id) if match_id != '' else -1
                if match_id == -1:
                    continue
                ids[cam][frame].append(number[match_id])
                dets[cam][frame].append(xyxy)
                num_dets += 1

        for t in range(num_timesteps):
            if len(ids[cam][t]):
                ids[cam][t] = np.array(ids[cam][t])
                dets[cam][t] = np.array(dets[cam][t])
            else:
                ids[cam][t] = np.empty(0).astype(int)
                dets[cam][t] = np.empty((0, 4))

    num_gt_ids = len(number)

    ids = ids if len(cams) > 1 else ids[cams[0]]
    dets = dets if len(cams) > 1 else dets[cams[0]]

    return num_gt_ids, ids, num_dets, dets

