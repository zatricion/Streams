from Stream import Stream
from Sender import Sender
import time
import random
import simplejson as json

class FileOrchestrator(object):
    """
    Appends the contents of files to corresponding streams in a random fashion.
    """
    def __init__(self, file_to_stream_list):
        self.file_to_stream_list = file_to_stream_list
    
    def signal(self):
        while len(self.file_to_stream_list):
            # Choose a random file to read from
            chosen = random.choice(self.file_to_stream_list)
            # Read to stream
            chosen.signal_some()
            # Remove files that have been finished
            self.file_to_stream_list = [file for file in self.file_to_stream_list if not file.eof]
            
            
class FileToStream(object):
    def __init__(self, in_file_name, output_stream):
        self.file_name = in_file_name
        self.output_stream = output_stream
        self.sender = Sender(self.file_name, self.output_stream)
        self.eof = False
        self.file_exists = True
        self.input = self.read_file(open(in_file_name, "r"))
                    
    def read_file(self, file_obj):
        while True:
            line = file_obj.readline()
            if not line:
                file_obj.close()
                break
            data = map(float, line.split())
            if len(data) > 1:
                yield data
            else:
                yield data[0]
    
    def send_to(self, q):
        self.sender.send_to(q)
    
    def signal_some(self, n=10):
        if self.file_exists:
            for dummy in range(n):
                try:
                    self.output_stream.append(self.input.next())
                except StopIteration:
                    self.output_stream.close()
                    self.eof = True
                    break
        else:
            self.output_stream.append("start")
            self.eof = True

    def signal(self):
        if self.file_exists:
            for item in self.input:
                self.output_stream.append(item)
            self.output_stream.close()
            self.eof = True
        else:
            self.output_stream.append("start")
            self.eof = True

class JSONFileToStream(object):
    def __init__(self, in_file_name, output_stream):
        self.file_name = in_file_name
        self.input_list_ptr = 0
        self.input_list = []
        self.output_stream = output_stream
        self.sender = Sender(self.file_name, self.output_stream)
        self.file_exists = True
        try:
            with open(in_file_name, "r") as f:
                self.input_list.extend(json.loads(f.read()))
                self.input_list.reverse()
        except:
            self.file_exists = False
        self.eof = False
    
    def send_to(self, q):
        self.sender.send_to(q)
    
    def signal_some(self, num = 1):
        self.signal()
        
    def signal(self):
        while self.input_list_ptr < len(self.input_list):
            self.output_stream.append(self.input_list[self.input_list_ptr])
            self.input_list_ptr += 1
        self.output_stream.close()
        self.eof = True
