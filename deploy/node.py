from twisted.application import service, internet
from twisted.python.log import ILogObserver
from twisted.internet import reactor, task, utils
import twisted

import sys, os
sys.path.append(os.path.dirname(__file__))
from kademlia.network import Server
from kademlia.log import Logger

import subprocess as sp
# from nodeManager import NodeManager
import json

logger = Logger()
    
def bootstrapDone(found, server):
    with open('../deploy/deploy_test.config', 'r') as f:
        server.set('deploy_config', f.read())
    logger.info("starting NodeMananger")
    # Have to user Twisted method for starting processes
    # manager = NodeManager(server)
    # manager.start()
    # http://twistedmatrix.com/documents/current/core/howto/process.html
    log = open('streams.log', 'w')
    cmd = ["python", "start_network.py"]
    p = reactor.spawnProcess(gp, cmd[0], cmd, env=None,
                             childFDs={0:'w', 1:'r', 2:2, 3:'w', log.fileno():'w'})

def makeService(config):
    bootstrap_addr = config["bootstrap"]
    port = int(config["port"])
    
    kserver = Server()
    
    if bootstrap_addr is not None:
        bootstrap_tuple = (bootstrap_addr, port)
        kserver.bootstrap([bootstrap_tuple]).addCallback(bootstrapDone, kserver)

    return internet.UDPServer(port, kserver.protocol)

if __name__ == "__main__":
    sp.call(["python", "start_network.py"])
