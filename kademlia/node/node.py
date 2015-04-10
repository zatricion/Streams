from twisted.application import service, internet
from twisted.python.log import ILogObserver
from twisted.internet import reactor, task

import sys, os
sys.path.append(os.path.dirname(__file__))
from kademlia.network import Server
from kademlia import log

def print_call(result):
    print result

def setDone(result, server):
    print server.get("beach")
    print server.get("a key").addCallback(print_call)

def bootstrapDone(found, server):
    server.set("a key", "a value")
    server.set("beach", "playa").addCallback(setDone, server)

def makeService(config):
    kserver = Server()
    kserver.bootstrap([(config["bootstrap"], int(config["port"]))]).addCallback(bootstrapDone, kserver)
    
    h = internet.UDPServer(7000, kserver.protocol)

    return h
