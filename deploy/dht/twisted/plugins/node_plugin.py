from zope.interface import implements

from twisted.python import usage
from twisted.plugin import IPlugin
from twisted.application.service import IServiceMaker

from ...node import node

class Options(usage.Options):
  optParameters = [["bootstrap", "b", None, "The ip address to use for bootstrapping."]
                  ,["port", "p", 8468, "The port to use for this server."]
                  ]

class NodeServiceMaker(object):
  implements(IServiceMaker, IPlugin)
  tapname = "node"
  description = "Creates a kademlia node with command line arguments."
  options = Options

  def makeService(self, config):
    """
    Construct a kademlia node.
    """
    return node.makeService(config)

serviceMaker = NodeServiceMaker()
