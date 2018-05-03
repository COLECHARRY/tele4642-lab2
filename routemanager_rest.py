import requests
import json


class APIError(Exception):
    pass


class SwitchObject:
    def __init__(self, dpid):
        self.dpidraw = dpid
        self.dpid = '{:06x}'.format(dpid)
        self.type = ''

    def settype(self, type):
        self.type = type

    def returnpod(self):
        return self.dpid[2:4]

    def __str__(self):
        return str(self.__dict__)


class SwitchObjectList:
    def __init__(self, switchlist):
        self.switches = switchlist
        self.k = 0

        for switch in self.switches:
            tmp = switch.dpid[:2]
            if int(tmp) > self.k:
                self.k = int(tmp)

        for switch in self.switches:
            tmp = switch.dpid[:2]
            if tmp == '{:02x}'.format(self.k):
                switch.type = 'core'
            else:
                x = int(switch.dpid[2:4])
                # TODO
                #for q in range(0, self.k)
                #if x == self.k-1:
                #    switch.setpod
                pass

    def getswitch(self, dpid):
        for switch in self.switches:
            if switch.dpid == dpid:
                return switch
            return None


class FlowEntry:
    def __init__(self, dpid, pri, match=None, actions=None):
        self.dpid = dpid
        self.priority = pri
        if match is None:
            self.match = {} # Dict
        else:
            self.match = match
        if actions is None:
            self.actions = [] # List of dicts
        else:
            self.actions = actions

    def set_outport(self, port):
        '''
        action = {"instructions": [{"type": "APPLY_ACTIONS","actions": [{
                    "max_len": 65535,
                    "port": port,
                    "type": "OUTPUT"
                }]}]}
        '''
        self.actions = {"type": "OUTPUT", "port": port}

    def setmatchip(self, ip, cidr):
        self.match = {"ipv4_dst": "{}/{}".format(ip, cidr), "eth_type": "0x0800"}

    def getdict(self):
        return self.__dict__


class APIManager():
    def __init__(self, svr="http://127.0.0.1:8080"):
        self.svr = svr

        r = self.getswitches()
        self.switchlist = SwitchObjectList(self.getswitches())
        self.k = self.switchlist.k

    def getswitches(self):
        rqurl = self.svr + "/stats/switches"
        r = requests.get(url=rqurl)
        if r.status_code != requests.codes.ok:
            raise APIError("Failed to connect to Ryu Controller")
        swl = []
        for x in r.json():
            swl.append(SwitchObject(x))
           # swl.append(sw)
        return swl

    def pushflowentry(self, fe):
        rqurl = self.svr + "/stats/flowentry/add"
        r = requests.post(url=rqurl, data=json.dumps((fe.getdict())))
        print("Pushing {}".format(json.dumps(fe.getdict())))
        if r.status_code != requests.codes.ok:
            raise APIError("Something went wrong")

    def pushroutetable(self):

        for switch in self.switchlist.switches:
            if switch.type != 'core':
                fel = []
                cidr = '8'
                pri = 1
                for q in range(self.k/2):
                    # Build suffix table entries
                    fel.append(FlowEntry(switch.dpidraw, pri))
                    sufp = (((q - 2 + int(switch.dpid[2:4])) % (self.k/2)) + self.k/2)
                    ip = '0.0.0.{}'.format(q+2)
                    fel[-1].setmatchip(ip, cidr)
                    fel[-1].set_outport(sufp+1)

                cidr = '24'
                pri = 10
                for q in range(self.k/2):
                    # Build prefix table entries
                    fel.append(FlowEntry(switch.dpidraw, pri))
                    prep = q
                    ip = '10.{}.{}.0'.format(int(switch.returnpod()), q)
                    fel[-1].setmatchip(ip, cidr)
                    fel[-1].set_outport(prep+1)

                # Push entry to switch
                for fe in fel:
                    self.pushflowentry(fe)

            else:
                pass

        print("Pushed all tables")

    def debug(self):
        print self.k


def main():
    apimanager = APIManager()
    res = apimanager.getswitches()
    for a in apimanager.switchlist.switches:
        print(a)

    apimanager.pushroutetable()
    apimanager.debug()


if __name__ == "__main__":
    main()
