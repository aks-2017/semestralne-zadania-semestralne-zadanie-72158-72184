import copy
import pox
import time
import pox.openflow.libopenflow_01 as of
from pox.core import core
from pox.lib.revent import *
from pox.lib.recoco import Timer
from collections import defaultdict
from pox.openflow.discovery import Discovery

log = core.getLogger()


class TestEvent(Event):
  def __init__(self, arg1):
    Event.__init__(self)
    self.routes = arg1


class Graph:
    def __init__(self):
        self.nodes = set()
        self.edges = defaultdict(set)
        self.links = []

    def add_node(self, value):
        if value not in self.nodes:
            self.nodes.add(value)

    def add_edge(self, from_node, to_node):
        if to_node not in self.edges[from_node]:
            self.edges[from_node].add(to_node)
        if from_node not in self.edges[to_node]:
            self.edges[to_node].add(from_node)

    def add_link(self, from_node, to_node): # from < to
        for link in self.links:
            if from_node == link[0] and to_node == link[1] or from_node == link[1] and to_node == link[0]:
		return
	new_link = (from_node, to_node)
        self.links.append(new_link)


class Node(object):
    def __init__(self, dpid, hops, parent):
        self.dpid = dpid
        self.num_hops = hops
        self.descendents = []
        self.parent = parent
    def add_branch(self, dpid, hops, parent):
         new = Node(dpid, hops, parent)
         self.descendents.append(new)
    def get_nodes(self):
        nodes = []
        nodes.append(self)

	items = len(nodes)
        i = 0
	while (i < items):
            for n in nodes[i].descendents:
                nodes.append(n)

            i += 1
            items = len(nodes)

        return nodes


class topoDiscovery(EventMixin):
    _core_name = "topoDiscovery"
    _eventMixin_events = set([TestEvent,])
    def __init__(self):
        self.graph = Graph()
        self.listenTo(core)
        Timer(10, self._handle_timer_elapse)

        def startup():
            core.openflow.addListeners(self, priority = 0)
            core.openflow_discovery.addListeners(self)

        core.call_when_ready(startup, ('openflow','openflow_discovery'))

    def _handle_LinkEvent(self, event): # handler for LLDP link event
        l = event.link
        sw1 = l.dpid1
        sw2 = l.dpid2

        self.graph.add_node(sw1)
        self.graph.add_edge(sw1, sw2)
        self.graph.add_link(sw1, sw2)

    def derive_paths(self, root): # dfs to find all paths in tree
        stack = [(root, [root.dpid])]
        while stack:
            (node, path) = stack.pop()
            for next in node.descendents:
                if len(next.descendents) == 0:
                    yield path + [next.dpid]
                else:
                    stack.append((next, path + [next.dpid]))

    def _handle_timer_elapse (self): # create tree from graph with Dijkstra
        tree = core.topoDiscovery.create_tree()
        paths = list(self.derive_paths(tree))
	print paths
        self.raiseEvent(TestEvent, paths) # raise event in latencyMonitor

    def create_tree(self):
        nodes = copy.deepcopy(self.graph.nodes)
        MP = nodes.pop()
        tree = Node(MP, 0, None)
        while nodes:
            current_node = nodes.pop()
            tree_nodes = tree.get_nodes()
            for node in tree_nodes: # all nodes in tree
                if node.dpid in self.graph.edges[current_node]: # node <--> current_node
                    for link in self.graph.links: # links, is <--> in tree ?
                        if node.dpid == link[0] and current_node == link[1] or node.dpid == link[1] and current_node == link[0]:
                            self.graph.links.remove(link) # <--> is now used
                            node.add_branch(current_node, node.num_hops + 1, node)
                            break

        return tree


def launch():
    core.registerNew(topoDiscovery)
