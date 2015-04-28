from twisted.internet import reactor
from twisted.python import log
from kademlia.network import Server
import sys

log.startLogging(sys.stdout)

def done(result):
    print "Key result:", result
    reactor.stop()

def setDone(result, server):
    server.get("a ke").addCallback(done)

server = Server()
server.listen(7002)
server.bootstrap([("10.0.1.7", 7000)]).addCallback(setDone, server)

reactor.run()
