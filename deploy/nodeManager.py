from multiprocessing import Process
import subprocess as sp

class NodeManager(Process):
    """
    Manages a node (don't know how yet).
    """
    def __init__(self, server):
        super(NodeManager, self).__init__()
        self.server = server
        with open('hostname.txt', 'r') as f:
            self.hostname = f.read()
    
    def run(self):
        print self.server.get('deploy_config')
        sp.call(["python", "runAnomaly.py", "deploy_test.any", "deploy_test.config", self.hostname])
        sp.call(["python", "start_network.py"])