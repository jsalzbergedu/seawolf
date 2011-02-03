
from missions.base import MissionBase
import entities

class TestMission(MissionBase):

    def init(self):
        self.entity_searcher.start_search([
            entities.PathEntity(),
        ])

    def step(self, object_found):
        print "Found Object: %s" % object_found
