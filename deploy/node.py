from twisted.application import service, internet
from twisted.python.log import ILogObserver
from twisted.internet import reactor, task

import sys, os
sys.path.append(os.path.dirname(__file__))
from kademlia.network import Server
from kademlia import log

import subprocess as sp

def bootstrapDone(found, server):
    sp.call(["python", "start_network.py"])

def makeService(config):
    bootstrap_addr = config["bootstrap"]
    port = int(config["port"])
    
    kserver = Server()

    if boostrap_addr is not None:
        bootstrap_tuple = (bootstrap_addr, port)
        kserver.bootstrap([bootstrap_tuple]).addCallback(bootstrapDone, kserver)

    return internet.UDPServer(port, kserver.protocol)

if __name__ == "__main__":
    sp.call(["python", "start_network.py"])
