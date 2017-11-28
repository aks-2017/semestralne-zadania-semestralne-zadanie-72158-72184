import pox
import pox.openflow.libopenflow_01 as of
from pox.core import core
from pox.lib.revent import *
from pox.lib.packet import *
from pox.lib.addresses import *
from pox.lib.util import *
from collections import namedtuple
from pox.openflow.of_json import *
import time

i_try = 1
Payload = namedtuple('Payload', 'pathId timeSent')
s_times = []
rtt = []
log = core.getLogger()
switches = dict()

class LinkDelayEvent(Event):
    def __init__(self):
	Event.__init__(self)

class MeasureRTTevent(Event):
    def __init__(self):
	Event.__init__(self)

class Monitor(EventMixin):
    _core_name = "latencyMonitor"
    _eventMixin_events = set([MeasureRTTevent,LinkDelayEvent,])
    def __init__(self, size=65000):
        self.listenTo(core)
        self.listenTo(core.topoDiscovery)
	self.listenTo(self, priority = -2)
	self.path_delays = []
	self.path_delays.append([])
	self.routes = []
	self.size = size
        def startup():
            core.openflow.addListeners(self, priority = 0)
            core.openflow.addListenerByName("ConnectionUp", self.start_switch)

        core.call_when_ready(startup, ('openflow', 'topoDiscovery'))

    def _handle_GoingUpEvent (self, event):
        pass

    def _handle_FlowStatsReceived(self, event):
        global s_times, rtt
        lt = time.time()

	dpid = event.connection.dpid
	duration = lt - s_times[dpid]
	if rtt[dpid] > (duration/2) :
        rtt[dpid] = (duration/2)

    def _handle_LinkDelayEvent(self, event):
        ip_pck = ipv4(protocol=253, #use for experiment and testing
			srcip = IPAddr("223.0.0.2"),
			dstip = IPAddr("224.0.0.255"))


	eth_packet = ethernet(type = ethernet.IP_TYPE)
	msg = of.ofp_packet_out()
	msg.actions.append(of.ofp_action_output(port = of.OFPP_ALL))
	a = [self.size]
	ip_payload = Payload(a, time.time())

	ip_pck.set_payload(repr(ip_payload))
	eth_packet.set_payload(ip_pck)

	for dpid in switches:
		eth_packet.src = struct.pack("!Q", switches[dpid].dpid)[2:]
		msg.data = eth_packet.pack()
		switches[dpid].send(msg)

	self.send_finish_rtt(IPAddr("0.0.0.1"))

        return EventHalt

    def send_finish_rtt(self, src_ip):
        ip_pck = ipv4(protocol=253, #use for experiment and testing
			srcip = src_ip,
			dstip = IPAddr("224.0.0.255"))


	eth_packet = ethernet(type = ethernet.IP_TYPE)
	msg = of.ofp_packet_out()
	msg.actions.append(of.ofp_action_output(port = of.OFPP_ALL))

	eth_packet.set_payload(ip_pck)

	msg.data = eth_packet.pack()
	switches[1].send(msg)


    def _handle_TestEvent(self, event): # receive connections and graph from topoDisc
        global s_times, rtt

	self.routes = event.routes

	rtt = [float('inf') for i in range(len(switches)+1)]
        s_times = [0 for i in range(len(switches)+1)]
	self.path_delays = [[0 for x in range(len(switches)+1)] for y in range(len(switches)+1)]

        msg = of.ofp_stats_request(body=of.ofp_flow_stats_request())
        for key,value in switches.iteritems():
            s_times[key] = time.time()
            value.send(msg)

	self.send_finish_rtt(IPAddr("0.0.0.0"))

        return EventHalt

    def start_switch (self, event):
        # This binds our PacketIn event listener
        event.connection.addListeners(self)
	switches[event.dpid] = event.connection

    def _handle_PacketIn(self, event):
	global i_try
    	timeRecv = time.time()
	packet = event.parsed

	ip_pck = packet.find(ipv4)

	if ip_pck.srcip == IPAddr("0.0.0.0"): # special flag packet
        self.raiseEvent(LinkDelayEvent)
        return EventHalt

	if ip_pck.srcip == IPAddr("0.0.0.1"): # special flag packet
            if i_try >= 4:
            for route in self.routes:
            delay = 0
            for i in range(len(route)-1):
                delay += self.path_delays[route[i]][route[i+1]]
            log.debug("Delay %s = %.2fms"%(route, delay*1000 ))
        i_try += 1
        return EventHalt

	if ip_pck.dstip == IPAddr("224.0.0.255"):
		payload = eval(ip_pck.payload)
		delay = timeRecv - payload.timeSent
		src_dpid = str_to_dpid(str(packet.src).replace(":", "-"))
		self.path_delays[src_dpid][event.dpid] = (delay-rtt[event.dpid]-rtt[src_dpid])


def launch():
  core.registerNew(Monitor)

