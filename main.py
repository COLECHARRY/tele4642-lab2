from mininet.topo import Topo
from mininet.net import Mininet
from mininet.util import irange, dumpNodeConnections
from mininet.log import setLogLevel
from mininet.cli import CLI

class ftt(Topo):
    def build(self, n=4):
        q = n * n / 4
        csw = []
        
        for x in range(q):
            # Build core switches
            csw.append(self.addSwitch('cs{}'.format(x), dpid='0000000000{:02x}{:04x}'.format(n,x)))
        
        for x in range(n):
            # Build pods
            asw = []
            
            for y in range(n/2):
                # Build Aggregate Switches
                asw.append(self.addSwitch('as{}{}'.format(x, y), dpid='0000000000{:02x}{:02x}01'.format(x, y + (n/2))))
                
                for z in range(n/2):
                    # Build links to core switches
                    self.addLink(asw[-1], csw[z + y*(n/2)], port1=(n/2) + z + 1, port2=x+1)
            
            for y in range(n/2):
                # Build Edge Switches
                esw = self.addSwitch('es{}{}'.format(x, y), dpid='0000000000{:02x}{:02x}01'.format(x, y))

                for z in range(n/2):
                    # Build hosts and host links
                    hst = self.addHost('h{}{}{}'.format(x,y,z), ip = '10.{}.{}.{}'.format(x, y, z+2))
                    self.addLink(hst, esw, port1=1, port2=z+1)
                    
                    # Build links to aggregate switches
                    self.addLink(esw, asw[z], port1=((n/2) + z + 1), port2=y+1)
   
topos = { 'ftt': ( lambda: ftt() ) }
            
def buildftt():
    tp = ftt(n=4)
    net = Mininet(tp)
    net.start()
    dumpNodeConnections(net.hosts)
    CLI(net)
    #net.pingAll()
    net.stop()
    

def main():
    setLogLevel('info')
    buildftt()


if __name__ == "__main__":
    main()
