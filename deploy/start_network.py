import time
import math
import multiprocessing as mp
import subprocess
from core.FileToStream import FileToStream, JSONFileToStream, FileOrchestrator
from core.Stream import Stream
from core.Sender import Sender
from core.AgentProcess import AgentProcess
from core.Agent import *


import kademlia.node.cove as cove

class ExternalReceiver(mp.Process):
    def __init__(self, instance, streams_to_procs):
        mp.Process.__init__(self)
        self.instance = instance
        self.streams_to_procs = streams_to_procs
        self.receivers = []
     
    def create_router(self, stream, proc):
        def router(ch, method, properties, body):
            proc.iq.put((stream, cove.unpack(value)))
        return router
    
    def run(self):
        for stream, proc in self.streams_to_procs.items():
            # create a process using cove.receive to get messages
            # from the rabbitmq queue for each incoming stream pushed to
            # the appropriate process in-queue (proc.iq)
            self.receivers.append(mp.Process(target=cove.receive, 
                                       args=(stream, self.create_router(stream, proc))))
            self.receivers[-1].start()


def main():
    modules = dict()    
    in_streams_dict = {'numbers.dat': ['p1'], 'main': ['p2']}
    out_streams_dict = {'out0': 'p2', 'main': 'p1'}
    external_in_streams = ['numbers.dat']
    external_out_streams = ['out0']
    external_processes = [u'p2']
    
    
    from network.p2 import p2
    modules['p2'] = p2
    
    from network.p1 import p1
    modules['p1'] = p1
    
    
    ### Connect modules
    for stream, from_module in out_streams_dict.iteritems():
        if stream in in_streams_dict:
            to_module_list = in_streams_dict[stream]
            for to_module in to_module_list:
                if from_module != to_module:
                    modules[from_module].connect_ostream_to_q(stream, modules[to_module].iq)
    
    ### Connect output
    output_q = mp.Queue()
    for stream in external_out_streams:
        m_name = out_streams_dict[stream]
        modules[m_name].connect_ostream_to_q(stream, output_q)
    
    ### Start modules
    for m in modules.values():
        m.start()
    
    ### Processes in this instance
    local_procs = list(set(modules.keys()) - set(external_processes))
    
    in_streams_to_procs = {stream: map(lambda x: modules[x], 
                                       filter(lambda x: x in local_procs, proc_name_list))
                                for stream, proc_name_list in in_streams_dict.items()}
    
    ### Receive from task queue
    if external_processes:
        ExternalReceiver('ChenPi', in_streams_to_procs).start()
    
    file_to_stream_list = []
    ### Hardcoded I/O, name input files <<stream_name>>
    for stream in external_in_streams:
        if stream in in_streams_to_procs:
            proc_list = in_streams_to_procs[stream]
            for proc in proc_list:
                s = Stream(stream, "Main")
                if stream.endswith('json'):
                    f = JSONFileToStream(stream, s)
                else:
                    f = FileToStream(stream, s)
                f.send_to(proc.iq)
                file_to_stream_list.append(f)
    
    output_proc = mp.Process(target=get_output, args=(output_q,))
    output_proc.start()
    
    # randomly read from files
    FileOrchestrator(file_to_stream_list).signal()
    output_proc.join()

def get_output(output_q):
    count = 0
    while True:
        next = output_q.get()
        count += 1
        stream_name, msg_value = next
        if msg_value == "CLOSE_STREAM":
            break
        print count, "stream_name, msg_value", stream_name, msg_value
        
        cove.send(stream, msg_value)
        

if __name__ == "__main__": 
    main()