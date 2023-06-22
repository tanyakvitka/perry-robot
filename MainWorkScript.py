import cv2
import numpy as np
import serial
import time
import math
from FunctionForProject import *

# Frame dimensions
HEIGHT, WIDTH = 800, 800

# Video stream source
url = r'http://192.168.61.136:4747/video'

# Capture video stream from camera
cap = cv2.VideoCapture(0)  # url)

# Connect to Arduino

try:
    ser = serial.Serial('COM11', 9600)
except Exception as e:
    ser = None
    print('Bluetooth модуль не найден, перевод в тестирующий режим...')

# Global variables
is_ball_left = False
is_ball_right = False
is_ball_detected = False
prev_position = None
ball_not_detected = False
middle_of_screen = WIDTH / 2
buffer_zone_in = 20
buffer_zone_out = 80
alpha = 0.4
timeSt = 0.0
timeGo = 0.0

Settings = DownloadSettings('ColorClassificatior.txt')

# Define zone dimensions and center
zone_center = (int(WIDTH / 2), int(HEIGHT / 2))
zone_width = int(WIDTH / 4)

cv2.namedWindow('Frame')
cv2.createTrackbar('MinRadius', 'Frame', 0, 255, lambda x: None)
cv2.createTrackbar('ProcentFilling', 'Frame', 0, 100, lambda x: None)
cv2.createTrackbar('DedLineHight', 'Frame', 475, 475, lambda x: None)
cv2.createTrackbar('MaskNumber', 'Frame', 0, len(Settings) - 1, lambda x: None)

while True:
    # Capture a frame from video stream
    ret, frame = cap.read()
    frame = cv2.resize(frame, (620, 480))
    if not ret:
        continue

    listSet = UpdateSettings(Settings, cv2.getTrackbarPos('MaskNumber', 'Frame'))

    # Define color range for the ball
    lower_color = np.array(listSet[0], dtype=np.uint8)
    upper_color = np.array(listSet[1], dtype=np.uint8)
    IterErode = listSet[2]
    IterDilate = listSet[3]
    BlurIter = listSet[4]
    BlurGrade = listSet[5]

    middle_of_screen = len(frame[0]) / 2
    DedLineHeight = cv2.getTrackbarPos('DedLineHight', 'Frame')

    # Mirror the frame
    # frame = cv2.flip(frame, 1)

    frame = ConvLight(frame)
    frame = Blur(frame, BlurGrade, BlurIter)

    # Convert frame to Lab
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2Lab)

    # Create binary image to filter out pixels outside of the ball color range
    mask = cv2.inRange(hsv, lower_color, upper_color)

    # Apply morphological transformations to remove noise and fill holes in the binary image
    mask = cv2.erode(mask, None, IterErode)
    mask = cv2.dilate(mask, None, IterDilate)
    frout = mask.copy()
    frout = cv2.bitwise_and(frame, frame, mask=mask)

    cv2.imshow("Frame", frout)

    contours, _ = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Find the largest circle contour if any exist
    max_contour = None
    max_contour1 = None
    max_contour_area = 0
    (center, radius) = ((0, 0), 0)
    for contour in contours:
        area = cv2.contourArea(contour)
        if area > max_contour_area:
            ((x, y), radius) = cv2.minEnclosingCircle(contour)
            center = (int(x), int(y))
            radius = int(radius)
            if (radius > cv2.getTrackbarPos('MinRadius', 'Frame')):
                max_contour1 = contour
            if (radius > cv2.getTrackbarPos('MinRadius', 'Frame')) and (
                    area / (math.pi * (radius ** 2)) > cv2.getTrackbarPos('ProcentFilling', 'Frame') / 100):
                max_contour_area = area
                max_contour = contour

    if max_contour1 is not None:
        ((xm, ym), r) = cv2.minEnclosingCircle(max_contour1)
        cv2.circle(frame, (int(xm), int(ym)), int(r), (100, 100, 100), 3)

    # Ball tracking system 
    if max_contour is not None:
        ((x, y), radius) = cv2.minEnclosingCircle(max_contour)
        center = (int(x), int(y))
        radius = int(radius)

        timeGo = time.time() - timeSt
        if (timeGo > 0.5):
            # Determine if ball is inside zone
            color = (0, 255, 255)

            is_ball_left = False
            is_ball_right = False

            if ((center[0] >= middle_of_screen - buffer_zone_in) and (center[0] <= middle_of_screen + buffer_zone_in)):
                is_ball_detected = True

            if (center[0] // middle_of_screen > 0) and (not is_ball_detected):
                is_ball_left = True
            elif (not is_ball_detected):
                is_ball_right = True
            else:
                color = (0, 0, 255)

            # Only send movement command once per buffer zone transition
            if (prev_position != [is_ball_left, is_ball_right]) and (center[1] <= DedLineHeight):
                if is_ball_left:
                    Move('L', ser)
                    print("Robot should move left")
                elif is_ball_right:
                    Move('R', ser)
                    print("Robot should move right")
                else:
                    Move('S', ser)
                    print("Robot should move straight")
                prev_position = [is_ball_left, is_ball_right]

            if (center[0] < middle_of_screen - buffer_zone_out) or (center[0] > middle_of_screen + buffer_zone_out):
                is_ball_detected = False

            ball_not_detected = True

            if (center[1] <= DedLineHeight):
                cv2.circle(frame, center, radius, color, 2)
                cv2.circle(frame, center, 5, (0, 0, 255), -1)

    # If ball is not detected, print movement command to steer robot towards ball
    else:
        timeSt = time.time()
        if ball_not_detected:
            Move('O', ser)
            print("Ball not detected")
            ball_not_detected = False
        prev_position = None

    # Display modified frame
    img = frame.copy()
    cv2.rectangle(img, (len(frame[0]) // 2 - buffer_zone_out, 0), (len(frame[0]) // 2 + buffer_zone_out, DedLineHeight),
                  (0, 0, 200), -1)
    cv2.rectangle(img, (len(frame[0]) // 2 - buffer_zone_in, 0), (len(frame[0]) // 2 + buffer_zone_in, DedLineHeight),
                  (0, 200, 0), -1)
    cv2.rectangle(img, (0, DedLineHeight), (len(frame[0]), DedLineHeight + 5), (200, 200, 0), -1)
    frame = cv2.addWeighted(img, alpha, frame, 1 - alpha, 0)

    cv2.imshow("Out", frame)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        Move('O', ser)
        print("Script is Over")
        break

# Release resources
cap.release()
cv2.destroyAllWindows()
