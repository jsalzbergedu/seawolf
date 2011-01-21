
import seawolf as sw

__all__ = ["mixer"]

class Mixer(object):
    def set_forward(rate):
        sw.notify.send("THRUSTER_REQUEST Forward %.4f" % (rate,))
        
    def set_strafe(rate):
        sw.notify.send("THRUSTER_REQUEST Strafe %.4f" % (rate,))
            
    def set_yaw(rate):
        sw.notify.send("THRUSTER_REQUEST Yaw %.4f" % (rate,))
                
    def set_depth(rate):
        sw.notify.send("THRUSTER_REQUEST Depth %.4f" % (rate,))
                    
    def set_pitch(rate):
        sw.notify.send("THRUSTER_REQUEST Pitch %.4f" % (rate,))
                        
    forward = property(lambda: 0, set_forward)
    strafe = property(lambda: 0, set_strafe)
    yaw = property(lambda: 0, set_yaw)
    depth = property(lambda: 0, set_depth)
    pitch = property(lambda: 0, set_pitch)

mixer = Mixer()
