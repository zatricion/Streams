from twisted.application import service, internet
from twisted.python.log import ILogObserver
from twisted.internet import reactor, task

import sys, os
sys.path.append(os.path.dirname(__file__))
from kademlia.network import Server
from kademlia import log

import subprocess as sp
from nodeManager import NodeManager
import json

def bootstrapDone(found, server):
    # sp.call(["python", "start_network.py"])
    manager = NodeManager(server)
    manager.start()

def makeService(config):
    bootstrap_addr = config["bootstrap"]
    port = int(config["port"])
    
    kserver = Server()

    if bootstrap_addr is not None:
        bootstrap_tuple = (bootstrap_addr, port)
        kserver.bootstrap([bootstrap_tuple]).addCallback(bootstrapDone, kserver)
    
    else:
        with open('../deploy/deploy_test.config', 'r') as f:
            kserver.set('deploy_config', f.read())

    return internet.UDPServer(port, kserver.protocol)

if __name__ == "__main__":
    sp.call(["python", "start_network.py"])
