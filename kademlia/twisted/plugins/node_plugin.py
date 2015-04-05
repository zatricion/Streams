from zope.interface import implements

from twisted.python import usage
from twisted.plugin import IPlugin
from twisted.application.service import IServiceMaker
from twisted.application import service, internet
from twisted.python.log import ILogObserver
from twisted.internet import reactor, task

import sys, os
sys.path.append(os.path.dirname(__file__))
from kademlia.network import Server
from kademlia import log

class Options(usage.Options):
  optParameters = [["bootstrap", "b", None, "The ip address to use for bootstrapping."]
                  ,["port", "p", 8468, "The port to use for this server."]
                  ]

class NodeServiceMaker(object):
  implements(IServiceMaker, IPlugin)
  tapname = "node"
  description = "Creates a kademlia node with command line arguments."
  options = Options

  def makeService(self, options):
    """
    Construct a kademlia node.
    """
    application = service.Application("kademlia")
    application.setComponent(ILogObserver, log.FileLogObserver(sys.stdout, log.INFO).emit)

    if os.path.isfile('cache.pickle'):
      kserver = Server.loadState('cache.pickle')
    else:
      kserver = Server()
      kserver.saveStateRegularly('cache.pickle', 10)

    kserver.bootstrap([options["bootstrap"], int(options["port"])])
    server = internet.UDPServer(int(options["port"]), kserver.protocol)
    server.setServiceParent(application)
    
    return server

serviceMaker = NodeServiceMaker()
