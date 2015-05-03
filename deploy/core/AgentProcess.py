import multiprocessing
from Stream import Stream
from Sender import Sender
from Agent import *

class AgentProcess(multiprocessing.Process):
    def __init__(self, name, in_stream_list, out_stream_list,
                 network_generation_function):
        multiprocessing.Process.__init__(self)
        self.name = name
        self.closed = False
        self.istream_list = [Stream(name, self.name) for name in in_stream_list]
        self.ostream_list = [Stream(name, self.name) for name in out_stream_list]
        self.iq = multiprocessing.Queue()
        self.h = network_generation_function

        self.ostream_to_sender_dict = dict()
        self.name_to_istream_dict = dict()
        for s in self.istream_list:
            self.name_to_istream_dict[s.name] = s
        for s in self.ostream_list:
            self.ostream_to_sender_dict[s.name] = Sender(self.name, s)
        self.h(self.istream_list, self.ostream_list)

    def connect_ostream_to_q(self, ostream_name, q):
        self.ostream_to_sender_dict[ostream_name].send_to(q)

    def run(self):
        while True:
            if all(s.closed for s in self.istream_list):
                self.closed = True
                break
            stream_name, msg_value = self.iq.get()
            stream = self.name_to_istream_dict[stream_name]
            if msg_value == "CLOSE_STREAM":
                stream.close()
            else:
                stream.extend(msg_value)
        for s in self.ostream_list: s.close()
        return