from mininet.topo import Topo
from mininet.net import Mininet
from mininet.util import dumpNodeConnections
from mininet.log import setLogLevel
from mininet.cli import CLI
from mininet.node import RemoteController


class ftt(Topo):
    def build(self, n=4):
        csw = []
        i = 0
        for x in range(n/2):  # Build core switches
            for y in range(n/2):
                csw.append(self.addSwitch('cs{}'.format(i), dpid='{}{:02x}{:02x}{:02x}'.format((5*'00'), n, x+1, y+1)))
                i += 1
        for x in range(n):  # Build pods
            asw = []
            for y in range(n/2):  # Build Aggregate Switches
                asw.append(self.addSwitch('as{}{}'.format(x, y), dpid='0000000000{:02x}{:02x}01'.format(x, y + (n/2))))
                for z in range(n/2):  # Build links to core switches
                    self.addLink(asw[-1], csw[z + y*(n/2)], port1=(n/2) + z + 1, port2=x+1)
            for y in range(n/2):  # Build Edge Switches
                esw = self.addSwitch('es{}{}'.format(x, y), dpid='0000000000{:02x}{:02x}01'.format(x, y))
                for z in range(n/2):  # Build hosts and host links
                    hst = self.addHost('h{}{}{}'.format(x,y,z), ip = '10.{}.{}.{}'.format(x, y, z+2))
                    self.addLink(hst, esw, port1=1, port2=z+1)
                    self.addLink(esw, asw[z], port1=((n/2) + z + 1), port2=y+1)  # Build links to aggregate switches


topos = {'ftt': (lambda: ftt())}


def main():
    n = 4
    setLogLevel('info')
    tp = ftt(n=n)
    net = Mininet(tp, controller=RemoteController(ip='127.0.0.1', name='RyuController'), autoStaticArp=True)
    net.start()

    dumpNodeConnections(net.hosts)
    # net.staticArp()  # Not needed if autoStaticArp=True
    CLI(net)
    net.stop()


if __name__ == "__main__":
    main()
