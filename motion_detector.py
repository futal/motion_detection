from __future__ import print_function
import argparse
import datetime
import time

import cv2

import imutils

parser = argparse.ArgumentParser()
parser.add_argument('video', metavar='VIDEO', nargs='?', default='None', help='Path to the video file')
parser.add_argument('-a', '--min-area', type=int, default=300, help='minimum area size')
parser.add_argument('-s', '--start', metavar='SEC', type=int, default=0, help='start time in seconds')
args = parser.parse_args()

if args.video is None:
    camera = cv2.VideoCapture(0)
    time.sleep(0.25)
else:
    camera = cv2.VideoCapture(args.video)
    camera.set(cv2.cv.CV_CAP_PROP_POS_MSEC, args.start*1000)
    
firstFrame = None
status = 'Unoccupied'

while True:
    (grabbed, frame) = camera.read()

    if not grabbed:
        break
    
    frame = imutils.resize(frame, width=480)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (21, 21), 0)
    
    if firstFrame is None:
        firstFrame = gray
        continue
    
    frameDelta = cv2.absdiff(firstFrame, gray)
    thresh = cv2.threshold(frameDelta, 25, 255, cv2.THRESH_BINARY)[1]
    
    thresh = cv2.dilate(thresh, None, iterations=2)
    (cnts, _) = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    for c in cnts:
        if cv2.contourArea(c) < args.min_area:
            if status == 'Occupied':
                status = 'Unoccupied'
                print(camera.get(cv2.cv.CV_CAP_PROP_POS_MSEC), ':', status)
            continue
        (x, y, w, h) = cv2.boundingRect(c)
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        if status == 'Unoccupied':
            status = 'Occupied'
            print(camera.get(cv2.cv.CV_CAP_PROP_POS_MSEC), ':', status)
    
    #cv2.putText(frame, 'Room Status: {}'.format(status), (10, 20),
              #cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
    #cv2.putText(frame, datetime.datetime.now().strftime('%A %d %B %Y %I:%M:%S%p'),
              #(10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)
    #cv2.imshow('Security Feed', frame)
    #cv2.imshow('Thresh', thresh)
    #cv2.imshow('Frame Delta', frameDelta)
    key = cv2.waitKey(1) & 0xFF
    
    if key == ord('q'):
        break
    
camera.release()
cv2.destroyAllWindows()
