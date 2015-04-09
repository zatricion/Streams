from twisted.application import service, internet
from twisted.python.log import ILogObserver
from twisted.internet import reactor, task

import sys, os
sys.path.append(os.path.dirname(__file__))
from kademlia.network import Server
from kademlia import log

application = service.Application("kademlia")
application.setComponent(ILogObserver, log.FileLogObserver(sys.stdout, log.INFO).emit)

if os.path.isfile('cache.pickle'):
    kserver = Server.loadState('cache.pickle')
else:
    kserver = Server()

def nextThing(res, server):
  server.set('a', 'b')
  

# kserver.bootstrap(["2601:8:ac00:b8d:ba27:ebff:feb0:6365", 5768])
kserver.bootstrap(["10.0.1.7", 7000])
kserver.saveStateRegularly('cache.pickle', 10)

server = internet.UDPServer(7000, kserver.protocol)
server.setServiceParent(application)
