
import seawolf

from time import time


class MissionControlReset(Exception):

    '''Indicates that a mission reset was signaled from an outside source.'''
    pass


class MissionBase(object):

    '''A base class for missions.'''

    def register_mission_controller(self, mission_controller):
        ''' Called by the mission controller when the mission is added.'''
        self.mission_controller = mission_controller
        self.process_manager = mission_controller.process_manager

    def init(self):
        '''Called once right before the mission is executed.'''
        pass

    def set_entity_timeout(self, timeout):
        '''Gives the time to wait for an entity before calling step() anyways.

        The execute function will look at the timeout given and call step(None)
        when the timeout has passed to indicate that no entity has been found
        in the past timeout seconds.  It will then continue to call step(None)
        every timeout seconds until an entity is seen.
        '''
        self._entity_timeout = timeout

    def execute(self):
        '''Runs the mission.

        This is a blocking call that returns when the mission completes.
        '''

        if not hasattr(self, "timers"):
            self.timers = {}

        self._entity_timeout = getattr(self, "_entity_timeout", None)
        self._mission_done = getattr(self, "_mission_done", False)
        self._mission_fail = getattr(self, "_mission_fail", False)
        last_entity_timestamp = time()

        while not self._mission_done:

            if seawolf.var.get("MissionReset"):
                print "MISSION RESET"
                raise MissionControlReset()

            vision_data = self.process_manager.get_data(delay=0.05)

            self.step(vision_data)

            # Timer callbacks
            current_time = time()
            for name, (t, delay, callback, args) in self.timers.items():
                if t + delay <= current_time:
                    self.delete_timer(name)
                    callback(*args)

            if self._mission_fail:
                return False
        return True

    def finish_mission(self, *args, **kwargs):
        '''Marks the mission complete so self.execute() will return.

        This is an asynchronous alternative to having self.step() return True.
        Any arguments are accepted, but all are ignored.  This allows you to
        register this function as a callback for anything, such as a nav
        routine.
        '''
        self._mission_done = True

    def fail_mission(self, *args, **kwargs):
        self._mission_fail = True

    def step(self, entity_found):
        '''
        Called whenever an entity is found.

        This function is the brain of the mission object.  It receives an
        entity and processes it in order to navigate the robot.

        This is the only function that needs to be implemented in a subclass.
        '''
        raise NotImplementedError("A subclass must implement this method.")

    def set_timer(self, name, delay, callback, *args):
        if not hasattr(self, "timers"):
            self.timers = {}
        self.timers[name] = (time(), delay, callback, args)

    def delete_timer(self, name):
        if not hasattr(self, "timers"):
            self.timers = {}
        try:
            del self.timers[name]
        except KeyError:
            pass


class SearchMission(MissionBase):

    '''
    Does nothing but search and print entity results.  Useful for testing
    simulated entities.
    '''

    def __init__(self, entity_class, camera="forward"):
        self.entity_class = entity_class
        self.camera = camera

    def init(self):
        self.process_manager.start_process(self.entity_class, "search", self.camera, debug=True)

    def step(self, vision_data):

        if not vision_data:
            return

        data = vision_data['search']
        if data:
            print data
