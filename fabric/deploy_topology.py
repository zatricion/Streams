import time
from fabric.api import *
import fabric.contrib.files as fabfiles

RABBITMQ_USER = 'peter1'
RABBITMQ_PASS = 'rabbit'
RABBITMQ_VHOST = 'potter'
RABBITMQ_PORT = 7001

KADEMLIA_PORT = 50113

HOSTS = 'hosts_ipv4.txt'
env.forward_agent = True
env.key_filename = '~/.ssh/id_rsa'
env.abort_on_prompts = True
env.hostnames = {}
env.addrs = {}

def populate_hosts():
    for line in open(HOSTS, 'r'):
        if line.strip() and not line.startswith('#'):
            name, host, password = line.split()
            env.hosts.append(host)
            # env.passwords[host+':22'] = password
            env.hostnames[host.split('@')[1]] = name
            env.addrs[name] = host

@task
def deploy_streams():
    if not fabfiles.exists('Streams'):
        run('ssh-keyscan github.com >> ~/.ssh/known_hosts')
        run('git clone git@github.com:zatricion/Streams.git')
        with cd('Streams'):
            run('git checkout deployment')
            sudo('pip install -r requirements.txt')
    else:
        with cd('Streams'):
            run('git fetch --all')
            run('git reset --hard origin/deployment')
            sudo('pip install -r requirements.txt')
        
    with cd('Streams/deploy'):
        run('echo {0} > hostname.txt'.format(env.hostnames[env.host]))
    
        ## TODO: allow specification of a real config file
        run('python runAnomaly.py deploy_test.any deploy_test.config {0}'.format(env.hostnames[env.host]))

@task
def start_kademlia(ip, port=None):
    with cd('Streams/deploy/'):
        with settings(warn_only=True):
            run('kill `cat twistd.pid`')
        run('twistd -l deploy_test.log node -b {0} -p {1}'.format(ip, port))
        
@task
def start_kademlia_verbose(ip, port=None):
    with cd('Streams/deploy/'):
        with settings(warn_only=True):
            run('kill `cat twistd.pid`')
        run('twistd -l deploy_test.log -n node -b {0} -p {1}'.format(ip, port))
        
def create_local_node(port=None):
    with lcd('../deploy/'):
        with settings(warn_only=True):
            local('kill `cat twistd.pid`')
        local('twistd -l deploy_test.log node -p {0}'.format(port))

def kill_local_node():
    with lcd('../deploy/'):
        local('kill -9 `cat twistd.pid`')
 
def main():
  # start temporary kademlia node
  create_local_node(KADEMLIA_PORT)
  
  time.sleep(15)
  print "go"

  # get local ipv4 address for bootstrapping (deploying from macbook)
  my_ipv4 = local('ipconfig getifaddr en0', capture=True)
  
  # Get the repo
  execute(deploy_streams)

  # start Kademlia network
  execute(start_kademlia, my_ipv4, KADEMLIA_PORT, hosts=env.addrs["rpi0"]) 
  execute(start_kademlia, my_ipv4, KADEMLIA_PORT, hosts=env.addrs["rpi1"]) 

  # clean up
  kill_local_node()

if __name__ == '__main__':
  populate_hosts()
  main()
