import os

import cv2

p = "data/cards_img/"

for filename in os.listdir(p):
    path = os.path.join(p, filename)
    img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    img = img[13:155, 13:115]
    img[:, :, 3][img[:, :, 3] < 200] = 255
    cv2.imwrite(path, img)
