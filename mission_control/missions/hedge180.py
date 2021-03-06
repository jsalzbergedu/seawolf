
from __future__ import division

from vision import entities
from missions.base import MissionBase
import sw3, time

MISSION_TIMEOUT = 1200
TIMEOUT_ENABLED = True
DEGREE_PER_PIXEL = 0.10
STRAIGHT_TOLERANCE = 3  # In degrees
FORWARD_SPEED = 0.5
BACKUP_SPEED = -0.9
BACKUP_TIME = 13

SLOW_FORWARD_SPEED = 0.4
#DEPTH = 2
DELAY = 2
HEDGE_DEPTH = 10

class HedgeMission180(MissionBase):

    def __init__(self):
        # gate tracking variables
        self.gate_seen = 0
        self.gate_lost = 0
        self.mission_timeout = MISSION_TIMEOUT

    def init(self):
        # Set depth to hedge hight, but keep heading at same time
        sw3.nav.do(sw3.CompoundRoutine(
            sw3.Forward(0),
            sw3.HoldYaw(),
            sw3.SetDepth(HEDGE_DEPTH),
        ))

        # give some time for the dive to complete
        time.sleep(4)
        """
        current_depth = sw3.data.depth()
        while current_depth <= HEDGE_DEPTH - 3:
            print "changing depth ({}) to {}".format(current_depth, HEDGE_DEPTH)
            current_depth = sw3.data.depth()
        """


        # start vision
        self.process_manager.start_process(entities.GateEntity, "gate", "forward", debug=True)

        # go forward
        sw3.nav.do(sw3.CompoundRoutine(
            #sw3.HoldYaw(),
            sw3.Forward(FORWARD_SPEED),
        ))

    def step(self, vision_data):
        print "timeout = {}".format(self.mission_timeout)
        
        # enable timeouts if necessary
        if TIMEOUT_ENABLED:
            self.mission_timeout -= 1

        # if vision is busy processing, skip and wait for vision data.
        if not vision_data:
            return

        gate_data = vision_data['gate']

        if not gate_data:
            return

        print gate_data

        if gate_data and gate_data.left_pole and gate_data.right_pole:

            # capture the location of the gate center in the camera frame.
            gate_center = DEGREE_PER_PIXEL * (gate_data.left_pole + gate_data.right_pole) / 2  # degrees

            # If both poles are seen, point toward it then go forward.
            self.gate_seen += 1
            self.gate_lost = 0

            if abs(gate_center) < STRAIGHT_TOLERANCE:
                sw3.nav.do(sw3.CompoundRoutine([
                    sw3.Forward(FORWARD_SPEED),
                    sw3.HoldYaw()
                ]))
            else:
                print "Correcting Yaw", gate_center
                sw3.nav.do(sw3.CompoundRoutine([
                    sw3.RelativeYaw(gate_center),
                    sw3.Forward(SLOW_FORWARD_SPEED)
                ]))

        # if it has been seen alot, but has been lost, increment the lost counter
        elif self.gate_seen >= 15:
            self.gate_lost += 1

        # if gate_lost counter has gotten too high, it's definately gone. Move on.
        if self.gate_lost > 30 or self.mission_timeout <= 0:
            # tell the user whether the gate was lost or the mission timed out
            print("Gate lost: %s , timeout: %s" % (self.gate_lost>5, self.mission_timeout <= 0))

            # print the timeout if necessary.
            if self.mission_timeout <= 0:
                print "Gate Mission Timeout!"

            # pretty much just a dummy message just to show that we're moving on.
            print "Heading Locked"

            # move on to the next state, because we know at this point that
            # we're pretty much in front of the hedge task and ready to do a 180.
            self.pass_with_style()

            # terminate the mission. move on.
            print "hi"
            self.finish_mission()
            return

            
    
    def pass_with_style(self):
        """the code for turning the robot, and passing through the hedge
        with style."""
        turn_routine = sw3.RelativeYaw(180)
        stop_routine = sw3.Forward(0, 0.1)
        backup_routine = sw3.Forward(BACKUP_SPEED, BACKUP_TIME)

        # stop
        sw3.nav.do(stop_routine)
        time.sleep(1)
        

        # 180
        sw3.nav.do(
            stop_routine,
            turn_routine,)              # do a 180
        time.sleep(10)

        sw3.nav.do(backup_routine)             # backup
        time.sleep(BACKUP_TIME)
        time.sleep(1)

        sw3.nav.do(stop_routine)               # stop
        time.sleep(1)

        print "doing the 2nd 180"
        sw3.nav.do(sw3.RelativeYaw(180))                # do another 180
        time.sleep(10)

        print "done"
    
        
        
