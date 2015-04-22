import multiprocessing
from Stream import Stream

class Sender(object):
    def __init__(self, agent_name, input_stream):
        self.istream = input_stream
        self.qlist = []
        self.istream.reader(self)
        self.istream.call(self)
        self.agent_name = agent_name
        
    def send_to(self, q):
        self.qlist.append(q)
        
    def signal(self, stream=None):
        if self.istream.closed:
            for q in self.qlist: q.put((self.istream.name, "CLOSE_STREAM",))
            return
        start = self.istream.start[self]
        end = self.istream.end
        for q in self.qlist: q.put(
                (self.istream.name, self.istream.recent[start:end],))
        self.istream.set_start(self, end)
