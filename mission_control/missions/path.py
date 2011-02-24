
from __future__ import division
import math
from math import pi
from collections import deque

from missions.base import MissionBase
import entities
import sw3
from sw3 import util

# If the path's position is off by more than this much, turn towards it
RHO_CENTERING_THRESHOLD = 20  # pixel distance
THETA_CENTERING_THRESHOLD = 50 * (pi/180)  # radians

THETA_RECORD_LENGTH = 5  # How many path orientations to keep track of

CENTERED_THRESHOLD = 60
# The range of our angle measurements must be less than this to
# start orienting ourselves.
ORIENTATION_RANGE_THRESHOLD = 10 * (pi/180)

class PathMission(MissionBase):

    def __init__(self):
        self.orientation_measurements = deque(maxlen=THETA_RECORD_LENGTH)
        self.orienting = False
        self.centered_count = 0

    def init(self):
        self.entity_searcher.start_search([
            entities.PathEntity(),
        ])
        sw3.nav.do(sw3.CompoundRoutine([
            sw3.Forward(0.4), sw3.SetDepth(2)
        ]))

        self.reference_angle = sw3.data.imu.yaw*(pi/180)
        if self.reference_angle < 0:
            self.reference_angle = pi - self.reference_angle
        self.oriented = 0

    def step(self, entity_found):
        if self.orienting: return False

        x = entity_found.center[0]
        y = entity_found.center[1]
        position_rho = math.sqrt(x**2 + y**2)

        position_theta = math.atan2(x, y)
        print position_theta * 180/math.pi

        yaw_routine = None
        forward_routine = None

        if abs(y) >= CENTERED_THRESHOLD and \
            abs(position_theta) > THETA_CENTERING_THRESHOLD:

            # Point robot toward path, then go forward
            yaw_routine = sw3.RelativeYaw(position_theta * (180/pi))
            forward_routine = sw3.Forward(0.3)
            print "Correcting Yaw", position_theta * (180/pi)

        if not yaw_routine:
            if y > CENTERED_THRESHOLD:
                forward_routine = sw3.Forward(0.3)
                self.centered_count = 0
                print "Forward"
            elif y < -1*CENTERED_THRESHOLD:
                forward_routine = sw3.Forward(-0.3)
                self.centered_count = 0
                print "Backward"
            else:
                self.centered_count += 1
                forward_routine = sw3.Forward(0.1*y/CENTERED_THRESHOLD)
                print "CENTERED!!!!!!", 0.1*y/CENTERED_THRESHOLD

        # Collect angle data
        current_yaw = sw3.data.imu.yaw*(pi/180)
        if current_yaw < 0:
            current_yaw = pi - current_yaw
        #self.orientation_measurements.append((entity_found.theta + current_yaw) % (pi))

        wrong_direction = True
        if self.centered_count >= 1:
            #len(self.orientation_measurements) == THETA_RECORD_LENGTH and \
            #util.circular_range(self.orientation_measurements, pi) < ORIENTATION_RANGE_THRESHOLD:

            #self.start_orientation()
            opposite_direction = (pi + entity_found.theta) % (2*pi)
            if (opposite_direction - self.reference_angle) % pi < (entity_found.theta - self.reference_angle) % pi:
                entity_found.theta = opposite_direction
            else:
                wrong_direction = False

            yaw_routine = sw3.RelativeYaw((180/pi)*entity_found.theta)
            print "Orienting", (180/pi)*entity_found.theta

        if yaw_routine and forward_routine:
            sw3.nav.do(yaw_routine)
            sw3.nav.append(forward_routine)
        elif yaw_routine:
            sw3.nav.do(yaw_routine)
        elif forward_routine:
            sw3.nav.do(forward_routine)

        if not wrong_direction and abs(entity_found.theta) < 0.1:
            print "Oriented for", self.oriented
            self.oriented += 1
            if self.oriented > 4:
                return True
        else:
            self.oriented = 0

    def start_orientation(self):
        #self.entity_searcher.start_search([])

        path_direction = util.circular_average(self.orientation_measurements, pi)

        # Flip direction it will make path_direction closer to the reference angle.
        opposite_direction = (pi + path_direction) % (2*pi)
        if (opposite_direction - self.reference_angle) % pi < (path_direction - self.reference_angle) % pi:
            path_direction = opposite_direction

        turn_routine = sw3.SetYaw((180/pi)*path_direction)
        turn_routine.on_done(self.finish_mission)
        sw3.nav.do(turn_routine)
        sw3.nav.append(sw3.HoldYaw())
        print "Orienting to", (180/pi)*path_direction

        self.orienting = True