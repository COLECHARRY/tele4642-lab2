from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3


class FTTRouteTable(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(FTTRouteTable, self).__init__(*args, **kwargs)

    def add_flow_ip(self, dp, m_dip, pri, out_port):
        match = dp.ofproto_parser.OFPMatch(ipv4_dst=m_dip, eth_type=0x0800)
        actions = [dp.ofproto_parser.OFPActionOutput(out_port)]
        self.add_flow(dp, pri, match, actions)

    def add_flow(self, dp, pri, match, actions):
        instructions = [dp.ofproto_parser.OFPInstructionActions(dp.ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = dp.ofproto_parser.OFPFlowMod(
            datapath=dp, match=match, cookie=0, command=dp.ofproto.OFPFC_ADD, idle_timeout=0, hard_timeout=0,
            priority=pri, flags=dp.ofproto.OFPFF_SEND_FLOW_REM, instructions=instructions)
        dp.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def _packet_in_handler_init(self, ev):
        k = 4  # Topology k number
        port_offset = 1  # Number to offset ports by (0 -> 1 for example)
        msg = ev.msg
        dp = msg.datapath

        # Process switch based on DPID and build match/action list
        dpid_hex = '{:06x}'.format(dp.id)
        spod = int(dpid_hex[:2], 16)
        swnum = int(dpid_hex[-2:-4:-1], 16)

        match = dp.ofproto_parser.OFPMatch()
        actions = [dp.ofproto_parser.OFPActionOutput(dp.ofproto.OFPP_CONTROLLER, dp.ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(dp, 0, match, actions)

        if spod == k:  # Core Switch Tables
            pri = 1
            for i in range(k):
                port = i + port_offset
                ip = ('10.{}.0.0'.format(i), '255.255.0.0')
                self.add_flow_ip(dp, ip, pri, port)

        elif spod < k and swnum >= k/2:  # Aggregation Switch Tables
            pri = 1
            for q in range(k / 2):  # Build suffix table entries
                sufp = (((q - 2 + swnum) % (k / 2)) + k / 2) + port_offset
                ip = ('0.0.0.{}'.format(q + 2), '0.0.0.255')
                self.add_flow_ip(dp, ip, pri, sufp)
            pri = 10
            for q in range(k / 2):  # Build prefix table entries
                prep = q + port_offset
                ip = ('10.{}.{}.0'.format(spod, q), '255.255.255.0')
                self.add_flow_ip(dp, ip, pri, prep)

        elif spod < k and swnum < k/2:  # Edge Switch Tables
            pri = 10
            for i in range(k/2):  # Build host route entries
                port = i + port_offset
                ip = ('10.{}.{}.{}'.format(spod, swnum, i + 2))  # , '255.255.255.255')
                self.add_flow_ip(dp, ip, pri, port)
            pri = 1
            for i in range(k/2):  # Build local pod subnet entries
                port = (((i - 2 + swnum) % (k / 2)) + k / 2) + port_offset
                ip = ('0.0.0.{}'.format(i+2), '0.0.0.255')
                self.add_flow_ip(dp, ip, pri, port)

        print('Pushing flow entry to switch {:x}'.format(dp.id))
