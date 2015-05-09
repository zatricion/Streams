import time
from fabric.api import *
import fabric.contrib.files as fabfiles

RABBITMQ_USER = 'peter'
RABBITMQ_PASS = 'rabbit'
RABBITMQ_VHOST = 'potter'
RABBITMQ_PORT = 7001

HOSTS = 'hosts_ipv4.txt'
env.forward_agent = True
env.key_filename = '~/.ssh/streams_deploy'
env.abort_on_prompts = True
env.hostnames = {}
env.addrs = {}

def populate_hosts():
    for line in open(HOSTS, 'r'):
        if line.strip() and not line.startswith('#'):
            name, host, password = line.split()
            env.hosts.append(host)
            env.passwords[host+':22'] = password
            env.hostnames[host.split('@')[1]] = name
            env.addrs[name] = host

@task
def deploy_streams():
    if not fabfiles.exists('Streams'):
        run('git clone git@github.com:zatricion/Streams.git')
        with cd('Streams'):
            run('git checkout deployment')
    else:
        with cd('Streams'):
            run('git fetch --all')
            run('git reset --hard origin/deployment')
            sudo('pip install -r requirements.txt')
        
        with cd('Streams/deploy'):
            ## TODO: allow specification of a real config file
            run('python runAnomaly.py deploy_test.any deploy_test.config {0}'.format(env.hostnames[env.host]))

@task
def start_kademlia(ip, port=None):
    with cd('Streams/deploy/'):
        run('twistd -l deploy_test.log node -b {0} -p {1}'.format(ip, port))
        
@task
def start_kademlia_verbose(ip, port=None):
    with cd('Streams/deploy/'):
        run('twistd -l deploy_test.log -n node -b {0} -p {1}'.format(ip, port))
        
def create_local_node(port=None):
    with lcd('../deploy/'):
        local('twistd -l deploy_test.log node')
 
def main():
  # Get the repo
  execute(deploy_streams)

  # start temporary kademlia node
  create_local_node(RABBITMQ_PORT)

  # get local ipv4 address for bootstrapping (deploying from macbook)
  my_ipv4 = local('ipconfig getifaddr en0', capture=True)

  # start Kademlia network
  execute(start_kademlia, my_ipv4, RABBITMQ_PORT, hosts=env.addrs["ChenPi"]) 
  execute(start_kademlia_verbose, my_ipv4, RABBITMQ_PORT, hosts=env.addrs["rpi0"]) 


if __name__ == '__main__':
  populate_hosts()
  main()
