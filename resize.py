'''忽略長寬比例，將圖片resize成128x384'''
import numpy as np
import cv2
import os

path = 'run/NkustMTMC/v2.0/part6'
imgs_path = path + '/img'
save_path = path + '/img_resize'

for cam in os.listdir(imgs_path):
    if not os.path.exists(os.path.join(save_path, cam)):
        os.makedirs(os.path.join(save_path, cam))
    for img_name in os.listdir(os.path.join(imgs_path, cam)):
        img_path = os.path.join(imgs_path, cam, img_name)
        img = cv2.imread(img_path)
        # img, _, _ = letterbox(img, new_shape=(384, 128), color=(114, 114, 114), auto=False, scaleup=True)
        img = cv2.resize(img, (128, 384), interpolation=cv2.INTER_LINEAR)
        cv2.imwrite(os.path.join(save_path, cam, img_name), img)
        print(img_path)