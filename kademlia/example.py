from twisted.internet import reactor
from twisted.python import log
from kademlia.network import Server
import sys

log.startLogging(sys.stdout)

def done(result):
    print "Key result:", result
    reactor.stop()

def setDone(result, server):
    server.get("a key").addCallback(done)

def bootstrapDone(found, server):
    server.set("a key", "a value").addCallback(setDone, server)

server = Server()
server.listen(7000)
# server.bootstrap([("10.0.1.7", 7000)]).addCallback(bootstrapDone, server)
server.bootstrap([("10.0.1.7", 7000)])

reactor.run()
