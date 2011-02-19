
from __future__ import division
import math

import cv

from entities.base import VisionEntity
import libvision
from sw3.util import circular_average

GATE_BLACK = 0
GATE_WHITE = 1

def line_group_accept_test(line_group, line, max_range):
    '''
    Returns True if the line should be let into the line group.

    First calculates what the range of rho values would be if the line were
    added.  If the range is greater than max_range the line is rejected and
    False is returned.
    '''
    min_rho = line[0]
    max_rho = line[0]
    for l in line_group:
        if l[0] > max_rho:
            max_rho = l[0]
        if l[0] < min_rho:
            min_rho = l[0]
    return max_rho - min_rho < max_range

class GateEntity(VisionEntity):

    name = "GateEntity"
    camera_name = "forward"

    def __init__(self, color=GATE_WHITE):

        # Thresholds
        self.vertical_threshold = 0.2  # How close to verticle lines must be
        self.horizontal_threshold = 0.2  # How close to horizontal lines must be
        self.hough_threshold = 30
        self.adaptive_thresh_blocksize = 19
        if color is GATE_WHITE:
            self.adaptive_thresh = 10
        else:
            self.adaptive_thresh = 4
        self.max_range = 60

        self.color = color

        self.left_pole = None
        self.right_pole = None

    def initialize_non_pickleable(self, debug=True):

        if debug:
            self.create_trackbar("adaptive_thresh", 20)
            self.create_trackbar("hough_threshold", 100)

    def find(self, frame, debug=True):
        found_gate = False
        cv.Smooth(frame, frame, cv.CV_MEDIAN, 7, 7)

        # Adaptive Filter
        # We use a different adaptive threshold filter for the black and white
        # gate.  The black gate is based on the red channel, the white gate is
        # based on saturation.
        if self.color is GATE_BLACK:
            # Set binary image to have red channel
            binary = cv.CreateImage(cv.GetSize(frame), 8, 1)
            cv.SetImageCOI(frame, 2)  # Saturation Channel of Interest
            cv.Copy(frame, binary)  # Binary image now contains green channel
            cv.SetImageCOI(frame, 0)
        else:
            # Set binary image to have saturation channel
            hsv = cv.CreateImage(cv.GetSize(frame), 8, 3)
            binary = cv.CreateImage(cv.GetSize(frame), 8, 1)
            cv.CvtColor(frame, hsv, cv.CV_RGB2HSV)
            cv.SetImageCOI(hsv, 2)  # Saturation Channel of Interest
            cv.Copy(hsv, binary)  # Binary image now contains saturation channel
            cv.SetImageCOI(hsv, 0)

        cv.AdaptiveThreshold(binary, binary,
            255,
            cv.CV_ADAPTIVE_THRESH_MEAN_C,
            cv.CV_THRESH_BINARY_INV,
            self.adaptive_thresh_blocksize,
            self.adaptive_thresh,
        )

        # Morphology
        kernel = cv.CreateStructuringElementEx(3, 3, 1, 1, cv.CV_SHAPE_ELLIPSE)
        cv.Erode(binary, binary, kernel, 1)
        cv.Dilate(binary, binary, kernel, 1)
        if debug:
            color_filtered = cv.CloneImage(binary)

        # Get Edges
        cv.Canny(binary, binary, 30, 40)

        # Hough Transform
        line_storage = cv.CreateMemStorage()
        raw_lines = cv.HoughLines2(binary, line_storage, cv.CV_HOUGH_STANDARD,
            rho=1,
            theta=math.pi/180,
            threshold=self.hough_threshold,
            param1=0,
            param2=0
        )

        # Get vertical lines
        vertical_lines = []
        for line in raw_lines:
            if line[1] < self.vertical_threshold or \
                line[1] > math.pi-self.vertical_threshold:

                vertical_lines.append( (abs(line[0]), line[1]) )

        # Group vertical lines
        vertical_line_groups = []  # A list of line groups which are each a line list
        for line in vertical_lines:
            group_found = False
            for line_group in vertical_line_groups:

                if line_group_accept_test(line_group, line, self.max_range):
                    line_group.append(line)
                    group_found = True

            if not group_found:
                vertical_line_groups.append([line])

        # Average line groups into lines
        vertical_lines = []
        for line_group in vertical_line_groups:
            rhos = map(lambda line: line[0], line_group)
            angles = map(lambda line: line[1], line_group)
            line = (sum(rhos)/len(rhos), circular_average(angles, math.pi))
            vertical_lines.append(line)

        # Get horizontal lines
        horizontal_lines = []
        for line in raw_lines:
            dist_from_horizontal = (math.pi/2 + line[1]) % math.pi
            if dist_from_horizontal < self.horizontal_threshold or \
                dist_from_horizontal > math.pi-self.horizontal_threshold:

                horizontal_lines.append( (abs(line[0]), line[1]) )

        # Group horizontal lines
        horizontal_line_groups = []  # A list of line groups which are each a line list
        for line in horizontal_lines:
            group_found = False
            for line_group in horizontal_line_groups:

                if line_group_accept_test(line_group, line, self.max_range):
                    line_group.append(line)
                    group_found = True

            if not group_found:
                horizontal_line_groups.append([line])

        if len(horizontal_line_groups) is 1:
            self.seen_crossbar = True
            if debug:
                rhos = map(lambda line: line[0], line_group)
                angles = map(lambda line: line[1], line_group)
                line = (sum(rhos)/len(rhos), circular_average(angles, math.pi))
                horizontal_lines = [line]
        else:
            self.seen_crossbar = False
            horizontal_lines = []

        self.left_pole = None
        self.right_pole = None
        if len(vertical_lines) is 2:
            self.left_pole = round(min(vertical_lines[0][0], vertical_lines[1][0]), 2) - frame.width/2
            self.right_pole = round(max(vertical_lines[0][0], vertical_lines[1][0]), 2) - frame.width/2
        #TODO: If one pole is seen, is it left or right pole?

        if debug:
            cv.CvtColor(color_filtered, frame, cv.CV_GRAY2RGB)
            libvision.misc.draw_lines(frame, vertical_lines)
            libvision.misc.draw_lines(frame, horizontal_lines)

        if self.left_pole or self.right_pole or self.seen_crossbar:
            return True

    def __repr__(self):
        return "<GateEntity left_pole=%s right_pole=%s seen_crossbar=%s>" % \
            (self.left_pole, self.right_pole, self.seen_crossbar)
