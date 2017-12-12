from __future__ import print_function
import argparse
import datetime
import time
from threading import Thread
import sys
import cv2

import imutils

if sys.version_info >= (3, 0):
    from queue import Queue  # Python 3
else:
    from Queue import Queue  # Python 2



parser = argparse.ArgumentParser()
parser.add_argument('video', metavar='VIDEO', nargs='?', default=None, help='Path to the video file')
parser.add_argument('-a', '--min-area', type=int, default=300, help='minimum area size')
parser.add_argument('-s', '--start', metavar='SEC', type=int, default=0, help='start time in seconds')
args = parser.parse_args()


class FileVideoStream:
    def __init__(self, path=None, startTime=0, queueSize=128):
        """Initialise the video from the webcam or from a file starting at the specified unoccupied time.
        Initialise the queue"""
        if path is None:
            self.stream = cv2.VideoCapture(0)
            time.sleep(0.25)
        else:
            self.stream = cv2.VideoCapture(path)
            self.stream.set(cv2.cv.CV_CAP_PROP_POS_MSEC, startTime*1000)
        self.stopped = False  # should the thread be stopped or not
        self.queue = Queue(maxsize=queueSize)
        print('initialisation')

    def start(self):
        """Start a thread to read frames from the video stream"""
        t = Thread(target=self.update, args=())
        t.daemon = True
        t.start()
        print('thread started')
        return self

    def update(self):
        while True:
            if self.stopped:
                return
            if not self.queue.full():
                (grabbed, frame) = self.stream.read()
            if not grabbed:  # end of file
                self.stop()
                return
            self.queue.put(frame)

    def read(self):
        """Return the next frame in the queue"""
        return self.queue.get()
    
    def more(self):
        """Return True if there are still frames in the queue"""
        return self.queue.qsize() > 0
    
    def stop(self):
        """Stop the thread before the end of the video file"""
        self.stopped = True
        

stream = FileVideoStream(args.video, startTime=args.start).start()
time.sleep(1.0)
firstFrame = None
status = 'Unoccupied'
n = 0
print('loop starting')

while stream.more():
    frame = stream.read()
    if frame is None:
        break
    
    n += 1
    print('processing frame:', n)
    
    
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
                print(stream.get(cv2.cv.CV_CAP_PROP_POS_MSEC), ':', status)
            continue
        (x, y, w, h) = cv2.boundingRect(c)
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        if status == 'Unoccupied':
            status = 'Occupied'
            print(stream.get(cv2.cv.CV_CAP_PROP_POS_MSEC), ':', status)
    
    cv2.putText(frame, 'Room Status: {}'.format(status), (10, 20),
              cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
    cv2.putText(frame, datetime.datetime.now().strftime('%A %d %B %Y %I:%M:%S%p'),
              (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)
    cv2.imshow('Security Feed', frame)
    cv2.imshow('Thresh', thresh)
    cv2.imshow('Frame Delta', frameDelta)
    key = cv2.waitKey(1) & 0xFF
    
    if key == ord('q'):
        break



    
cv2.destroyAllWindows()
