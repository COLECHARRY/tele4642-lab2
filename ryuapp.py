from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, CONFIG_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
import array

class L2Switch(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(L2Switch, self).__init__(*args, **kwargs)

    def add_flow_ip(self, dp, m_dip, pri, out_port):

        '''
        :param dp: Datapath Object
        :param m_dip: Destination IP to match
        :param pri: Priority
        :param out_port: Output Port
        :return: None
        '''

        ofproto = dp.ofproto

        match = dp.ofproto_parser.OFPMatch(
            ipv4_dst=m_dip, eth_type=0x0800)
            # nw_dst_mask=m_mask)

        actions = [dp.ofproto_parser.OFPActionOutput(out_port)]
        instructions = [dp.ofproto_parser.OFPInstructionActions(dp.ofproto.OFPIT_APPLY_ACTIONS, actions)]

        mod = dp.ofproto_parser.OFPFlowMod(
            datapath=dp, match=match, cookie=0,
            command=ofproto.OFPFC_ADD, idle_timeout=0, hard_timeout=0,
            priority=pri,
            flags=ofproto.OFPFF_SEND_FLOW_REM, instructions=instructions)
        dp.send_msg(mod)

    def add_flow(self, dp, pri, match, actions):
        instructions = [dp.ofproto_parser.OFPInstructionActions(dp.ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = dp.ofproto_parser.OFPFlowMod(
            datapath=dp, match=match, cookie=0,
            command=dp.ofproto.OFPFC_ADD, idle_timeout=0, hard_timeout=0,
            priority=pri, flags=dp.ofproto.OFPFF_SEND_FLOW_REM, instructions=instructions
        )
        dp.send_msg(mod)

    # @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def _packet_in_handler_init(self, ev):
        k = 4
        port_offset = 1
        msg = ev.msg
        dp = msg.datapath
        # buf = packet.Packet(msg.data)

        # ofp = dp.ofproto
        # ofp_parser = dp.ofproto_parser
        # dpid = dp.id

        # Process switch based on DPID and build match/action list
        # print type(dpid)
        dpid_hex = '{:06x}'.format(dp.id)
        # print dpid_hex
        spod = int(dpid_hex[:2], 16)
        # print 'spod: ' + str(spod)
        swnum = int(dpid_hex[-2:-4:-1], 16)
        # print 'swnum: ' + str(swnum)
        # crnum = int(dpid_hex[-2:], 16)
        # print 'crnum: ' + str(crnum)

        match = dp.ofproto_parser.OFPMatch()
        actions = [dp.ofproto_parser.OFPActionOutput(dp.ofproto.OFPP_CONTROLLER,
                                                     dp.ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(dp, 0, match, actions)

        # Core Switch Tables
        if spod == k:
            # Do something
            pri = 1
            for i in range(k):
                port = i + port_offset
                ip = ('10.{}.0.0'.format(i), '255.255.0.0')
                self.add_flow_ip(dp, ip, pri, port)

        # Aggregation Switch Tables
        elif spod < k and swnum >= k/2:
            pri = 1
            for q in range(k / 2):
                # Build suffix table entries
                sufp = (((q - 2 + swnum) % (k / 2)) + k / 2) + port_offset
                ip = ('0.0.0.{}'.format(q + 2), '0.0.0.255')
                self.add_flow_ip(dp, ip, pri, sufp)

            pri = 10
            for q in range(k / 2):
                # Build prefix table entries
                prep = q + port_offset
                ip = ('10.{}.{}.0'.format(spod, q), '255.255.255.0')
                self.add_flow_ip(dp, ip, pri, prep)

        # Edge Switch Tables
        elif spod < k and swnum < k/2:
            pri = 10
            for i in range(k/2):
                # Build host route entries
                port = i + port_offset
                ip = ('10.{}.{}.{}'.format(spod, swnum, i + 2))  # , '255.255.255.255')
                self.add_flow_ip(dp, ip, pri, port)

            pri = 1
            for i in range(k/2):
                # Build local pod subnet entries
                port = (((i - 2 + swnum) % (k / 2)) + k / 2) + port_offset
                ip = ('0.0.0.{}'.format(i+2), '0.0.0.255')
                self.add_flow_ip(dp, ip, pri, port)

        print('Pushing flow entry to switch {:x}'.format(dp.id))
        # actions = [ofp_parser.OFPActionOutput(ofp.OFPP_FLOOD)]
        # out = ofp_parser.OFPPacketOut(datapath=dp, buffer_id=msg.buffer_id, in_port=msg.in_port, actions=actions)
        # dp.send_msg(out)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        datapath = ev.msg.datapath
        dpid = "{:06x}".format(datapath.id)
        # print('{} is receiving packets'.format(dpid))
        # print packet.Packet(array.array('B', ev.msg.data))
