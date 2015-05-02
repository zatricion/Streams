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
    kserver = Server()
    kserver.bootstrap([(config["bootstrap"], int(config["port"]))]).addCallback(bootstrapDone, kserver).addErrback(bootstrapDone, kserver)

    return internet.UDPServer(7000, kserver.protocol)

if __name__ == "__main__":
    sp.call(["python", "start_network.py"])
