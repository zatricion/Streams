from core.Stream import Stream
from core.Sender import Sender
from core.AgentProcess import AgentProcess
from core.Agent import *

def process_contents(ext_in_stream_list, ext_out_stream_list):
    stream_names = []
    internal_streams = {stream : Stream(stream, 'p1') for stream in stream_names}

    ext_in_stream_dict = {s.name : s for s in ext_in_stream_list}
    ext_out_stream_dict = {s.name : s for s in ext_out_stream_list}

    
    in_stream_names = ['numbers.dat']
    out_stream_names = ['main']
    
    Main_in_streams = []
    for name in in_stream_names:
        if name in ext_in_stream_dict:
            stream = ext_in_stream_dict[name]
        elif name in ext_out_stream_dict:
            stream = ext_out_stream_dict[name]
        else:
            stream = internal_streams[name]
        Main_in_streams.append(stream)
        
    Main_out_streams= []
    for name in out_stream_names:
        if name in ext_out_stream_dict:
            stream = ext_out_stream_dict[name]
        else:
            stream = internal_streams[name]
        Main_out_streams.append(stream)
    
    params = {}
    
    params['element_function'] =  lambda x: x
    
    
    
    
    
    
    
    AgentParametric(Main_in_streams, Main_out_streams, Main_in_streams,
                map_multiple_streams, params)
    
    

external_in_streams = ['numbers.dat']
external_out_streams = ['main']

p1 = AgentProcess('p1', 
                          external_in_streams,
                          external_out_streams,
                          process_contents)