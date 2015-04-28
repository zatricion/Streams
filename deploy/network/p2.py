from core.Stream import Stream
from core.Sender import Sender
from core.AgentProcess import AgentProcess
from core.Agent import *
import kademlia.node.cove as cove

def process_contents(ext_in_stream_list, ext_out_stream_list):
    CovertAgent(ext_in_stream_list, ext_out_stream_list, ext_in_stream_list,
                   'localhost', cove)

external_in_streams = ['main']
external_out_streams = ['out0']

p2 = AgentProcess('p2', 
                          external_in_streams,
                          external_out_streams,
                          process_contents)