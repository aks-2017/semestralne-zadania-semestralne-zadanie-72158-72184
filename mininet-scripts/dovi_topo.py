#!/usr/bin/python

from mininet.topo import Topo

class MyTopo( Topo ):
    "Simple topology example."

    #def __init__( self ):
    def build(self):
        "Create custom topo."

        # Initialize topology
        #Topo.__init__( self )

        # Add hosts and switches
        s1 = self.addSwitch( 's1' )
        s2 = self.addSwitch( 's2' )
        s3 = self.addSwitch( 's3' )
        s4 = self.addSwitch( 's4' )
        s5 = self.addSwitch( 's5' )
        s6 = self.addSwitch( 's6' )

        # Add links
        self.addLink( s1, s2 )
        self.addLink( s1, s5 )
        self.addLink( s2, s3 )
        self.addLink( s2, s4 )
        self.addLink( s3, s4 )
        self.addLink( s3, s6 )
        self.addLink( s4, s5 )
        self.addLink( s4, s6 )
        self.addLink( s5, s6 )


topos = { 'dovi_topo': MyTopo }

