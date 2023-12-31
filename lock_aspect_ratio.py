'''維持長寬比例，將圖片resize成128x384'''
import numpy as np
import cv2
import os

def letterbox(img, new_shape=(640, 640), color=(114, 114, 114), auto=True, scaleFill=False, scaleup=True, stride=32):
    # Resize and pad image while meeting stride-multiple constraints
    shape = img.shape[:2]  # current shape [height, width]
    if isinstance(new_shape, int):
        new_shape = (new_shape, new_shape)

    # Scale ratio (new / old)
    r = min(new_shape[0] / shape[0], new_shape[1] / shape[1])
    if not scaleup:  # only scale down, do not scale up (for better test mAP)
        r = min(r, 1.0)

    # Compute padding
    ratio = r, r  # width, height ratios
    new_unpad = int(round(shape[1] * r)), int(round(shape[0] * r))
    dw, dh = new_shape[1] - new_unpad[0], new_shape[0] - new_unpad[1]  # wh padding
    if auto:  # minimum rectangle
        dw, dh = np.mod(dw, stride), np.mod(dh, stride)  # wh padding
    elif scaleFill:  # stretch
        dw, dh = 0.0, 0.0
        new_unpad = (new_shape[1], new_shape[0])
        ratio = new_shape[1] / shape[1], new_shape[0] / shape[0]  # width, height ratios

    dw /= 2  # divide padding into 2 sides
    dh /= 2

    if shape[::-1] != new_unpad:  # resize
        img = cv2.resize(img, new_unpad, interpolation=cv2.INTER_LINEAR)
    top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
    left, right = int(round(dw - 0.1)), int(round(dw + 0.1))
    img = cv2.copyMakeBorder(img, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color)  # add border
    return img, ratio, (dw, dh)

path = 'run/NkustMTMC/v2.0/part6'
imgs_path = path + '/img'
save_path = path + '/img_letterbox'

for cam in os.listdir(imgs_path):
    if not os.path.exists(os.path.join(save_path, cam)):
        os.makedirs(os.path.join(save_path, cam))
    for img_name in os.listdir(os.path.join(imgs_path, cam)):
        img_path = os.path.join(imgs_path, cam, img_name)
        img = cv2.imread(img_path)
        img, _, _ = letterbox(img, new_shape=(384, 128), color=(114, 114, 114), auto=False, scaleup=True)
        cv2.imwrite(os.path.join(save_path, cam, img_name), img)
        print(img_path)