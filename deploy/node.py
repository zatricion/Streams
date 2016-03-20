from twisted.application import service, internet
from twisted.python.log import ILogObserver
from twisted.internet import reactor, task
from twisted.python import log

import sys, os
sys.path.append(os.path.dirname(__file__))
from kademlia.network import Server

import subprocess as sp
from nodeManager import NodeManager
import json

def printer(res):
    print res
    print "right"
    
def bootstrapDone(found, server, port):
    raise Exception("bootstrapDone called")
    log.info("attempting to set deploy config")
    with open('../deploy/deploy_test.config', 'r') as f:
        server.set('deploy_config', f.read()).addCallback(printer) 
    log.info("starting NodeMananger")
    manager = NodeManager(server)
    manager.start()

def makeService(config):
    bootstrap_addr = config["bootstrap"]
    port = int(config["port"])
    
    kserver = Server()
    
    log.info("starting service")
    if bootstrap_addr is not None:
        bootstrap_tuple = (bootstrap_addr, port)
        kserver.bootstrap([bootstrap_tuple]).addCallback(bootstrapDone, kserver)

    return internet.UDPServer(port, kserver.protocol)

if __name__ == "__main__":
    sp.call(["python", "start_network.py"])
