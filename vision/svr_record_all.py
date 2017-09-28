'''Show all SVR streams, and show any new streams that appear.'''

from __future__ import division
from time import time

import cv

import svr

import cv2

import libvision

import argparse

svr.connect()

open_streams = {} # Map stream names to stream objects
last_sources_update = 0  # Last time that the open_streams was updated
SOURCES_UPDATE_FREQUENCY = 5  # How many times per second to update sources

def getargs():
    parser = argparse.ArgumentParser('Record video streams. May be used in conjunciton with watch all.')
    parser.add_argument('filename', help='File that the stream gets recorded to.')
    parser.add_argument('stream', help='Stream to use.')
    args = parser.parse_args()
    print(args.stream)
    return (args.filename + '.avi', args.stream)

def record_frame(stream_name, stream, out, filename):
    frame = None
    try:
        frame = stream.get_frame()
    except svr.OrphanStreamExeption:
        # Closed Stream
        del open_streams[stream_name]
        cv.DestroyWindow(stream_name)
        print "Stream Closed:", stream_name
        
    if frame:
        if out.isOpened():
            raw_frame = libvision.cv_to_cv2(frame)
            out.write(raw_frame)
        else: # Closes out.isOpened()
            cv2.imwrite("{}{}{}.jpeg".format(stream_name,filename, i), raw_frame)
            i += 1


if __name__ == "__main__":
    (filename, stream_arg) = getargs()
    fourcc = cv2.cv.CV_FOURCC(*'XVID')
    out = cv2.VideoWriter(filename, fourcc, 20.0, (640,480))
    try:
        stream = svr.Stream(stream_arg)
        stream.unpause()
        print("Stream Opened: {}".format(stream_arg))
    except svr.StreamException:
        del stream
        print("Stream Closed: {}".format(stream_arg))

    while True:
        record_frame(stream_arg, stream, out, filename)
