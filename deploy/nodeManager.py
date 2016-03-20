from multiprocessing import Process
import subprocess as sp
import time

def printer(res):
    with open('deploy_test_written.config', 'w') as f:
        f.write(res)
    
class NodeManager(Process):
    """
    Manages a node (don't know how yet).
    """
    def __init__(self, server):
        super(NodeManager, self).__init__()
        self.server = server
        with open('hostname.txt', 'r') as f:
            self.hostname = f.readline()
    
    def run(self):
        # print "not doing anything"
        # self.server.get('deploy_config').addCallback(printer)
        print "running network"
        sp.call(["python", "runAnomaly.py", "deploy_test.any", "deploy_test.config", self.hostname])
        with open('stream.log', 'w') as f:
            sp.call(["python", "start_network.py"], stdout=f, stderr=sp.STDOUT)
