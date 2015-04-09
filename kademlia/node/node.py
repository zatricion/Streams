from twisted.application import service, internet
from twisted.python.log import ILogObserver
from twisted.internet import reactor, task

import sys, os
sys.path.append(os.path.dirname(__file__))
from kademlia.network import Server
from kademlia import log

# Easy configuration

def setDone(result, server):
    server.get("a key")

def bootstrapDone(found, server):
    server.set("a key", "a value").addCallback(setDone, server)

def makeService(config):
    kserver = Server()
    kserver.bootstrap([(config["bootstrap"], int(config["port"]))]).addCallback(bootstrapDone, kserver)
    
    h = internet.UDPServer(7000, kserver.protocol)

    return h
