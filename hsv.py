import cv2
import numpy as np
import time


def nothing(x):
    pass


cv2.namedWindow('Trackbars', cv2.WINDOW_NORMAL)
# cv2.createTrackbar('L - H', 'Trackbars', 0, 179, nothing)
# cv2.createTrackbar('L - S', 'Trackbars', 0, 255, nothing)
# cv2.createTrackbar('L - V', 'Trackbars', 0, 255, nothing)
# cv2.createTrackbar('U - H', 'Trackbars', 179, 179, nothing)
# cv2.createTrackbar('U - S', 'Trackbars', 255, 255, nothing)
# cv2.createTrackbar('U - V', 'Trackbars', 255, 255, nothing)
cv2.createTrackbar('L - H', 'Trackbars', 0, 240, nothing)
cv2.createTrackbar('L - S', 'Trackbars', 0, 240, nothing)
cv2.createTrackbar('L - V', 'Trackbars', 0, 240, nothing)
cv2.createTrackbar('U - H', 'Trackbars', 240, 240, nothing)
cv2.createTrackbar('U - S', 'Trackbars', 240, 240, nothing)
cv2.createTrackbar('U - V', 'Trackbars', 240, 240, nothing)

while True:
    img = cv2.imread('debug/header.png', cv2.IMREAD_COLOR)
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    r, g, b = cv2.split(rgb)

    l_h = cv2.getTrackbarPos('L - H', 'Trackbars')
    l_s = cv2.getTrackbarPos('L - S', 'Trackbars')
    l_v = cv2.getTrackbarPos('L - V', 'Trackbars')
    u_h = cv2.getTrackbarPos('U - H', 'Trackbars')
    u_s = cv2.getTrackbarPos('U - S', 'Trackbars')
    u_v = cv2.getTrackbarPos('U - V', 'Trackbars')

    lower_range = np.array([l_h * 179 / 240, l_s * 255 / 240, l_v * 255 / 240])
    upper_range = np.array([u_h * 179 / 240, u_s * 255 / 240, u_v * 255 / 240])

    mask = cv2.inRange(hsv, lower_range, upper_range)
    mask = cv2.bitwise_not(mask, mask)

    res = cv2.bitwise_and(img, img, mask=mask)

    mask_3 = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)

    stacked = np.hstack((mask_3, img, res))
    #stacked = np.hstack((r, g, b))
    #stacked = np.vstack((stacked, rgb_stack))

    cv2.imshow('Trackbars', cv2.resize(stacked, None, fx=1, fy=1))

    key = cv2.waitKey(1)
    if key == 27:
        break

cv2.destroyAllWindows()
