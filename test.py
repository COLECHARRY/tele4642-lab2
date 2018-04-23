from mininet.topo import Topo
from mininet.net import Mininet
from mininet.util import irange, dumpNodeConnections
from mininet.log import setLogLevel

class ftt(Topo):
    def build(self, n=4):
        
        sw = self.addSwitch('s1', dpid = '0000000000000001')
        
        host1 = self.addHost('h1', ip = '10.0.0.2')
        host2 = self.addHost('h2', ip = '10.0.0.3')
        
        self.addLink(sw, host1, port1=1, port2=1)
        self.addLink(sw, host2, port1=2, port2=1)
   
topos = { 'ftt': ( lambda: ftt() ) }