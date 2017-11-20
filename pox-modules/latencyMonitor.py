import pox  
import pox.openflow.libopenflow_01 as of  
from pox.core import core  
from pox.lib.revent import *

class Monitor(EventMixin):  
    def __init__(self):
        self.listenTo(core)
        self.listenTo(core.topoDiscovery)

        def startup():
            core.openflow.addListeners(self, priority = 0)
            #core.openflow_discovery.addListenerByName("LinkEvent", self.s)
            core.openflow.addListenerByName("ConnectionUp", self.start_switch)
    
        core.call_when_ready(startup, ('openflow', 'topoDiscovery'))

    def _handle_GoingUpEvent (self, event):
        print "This is in subsriber, what is this for?\n"

    def _handle_TestEvent(self,event): # receive connections and graph from topoDisc
        print "Test Event is raised,I heard TestEvent\n"
        #print "EventPar:", event.par
        #print "EventPar:", event.par2
        #event.eventMethod()
        return

    def start_switch (self, event):
        # This binds our PacketIn event listener
        event.connection.addListeners(self) 
        print 'start: ' + str(event.connection.dpid)
        pass
        #print dir(event.connection)
        #print(event.dpid)
        #log.debug("Controlling ---- %s" % (event.connection,))
        #Tutorial(event.connection)

    def _handle_PacketIn(event):
        packet = event.parsed
        print dir(packet)
        print type(packet)
        # core.openflow.addListenerByName("PacketIn", _handle_PacketIn)


def launch():
  core.registerNew(Monitor)

