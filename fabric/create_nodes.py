import time
from fabric.api import *
import fabric.contrib.files as fabfiles

RABBITMQ_USER = 'peter'
RABBITMQ_PASS = 'rabbit'
RABBITMQ_VHOST = 'potter'
RABBITMQ_PORT = 7000

HOSTS = 'hosts_ipv4.txt'
env.forward_agent = True
env.key_filename = '~/.ssh/streams_deploy'
env.abort_on_prompts = True
env.hostnames = {}

def populate_hosts():
    for line in open(HOSTS, 'r'):
        if line.strip() and not line.startswith('#'):
            name, host, password = line.split()
            env.hosts.append(host)
            env.passwords[host+':22'] = password
            env.hostnames[host.split('@')[1]] = name
         
@task
def update():
    sudo('apt-get update')
    sudo('apt-get -y upgrade')
    sudo('echo "deb http://www.rabbitmq.com/debian/ testing main" >> /etc/apt/sources.list')
    sudo('curl http://www.rabbitmq.com/rabbitmq-signing-key-public.asc -o rabbitmq-signing-key-public.asc')
    sudo('cat rabbitmq-signing-key-public.asc | apt-key add -')
    sudo('apt-get update')
    
@task
def clone_deploy():
    with settings(prompts={'Are you sure you want to continue connecting (yes/no)? ' : 'yes'}):
        # get git
        sudo('apt-get install -y git')

        # get pip
        sudo('apt-get install -y curl')
        if not fabfiles.exists('get-pip.py'):
            sudo('curl -O https://bootstrap.pypa.io/get-pip.py')
            sudo('python get-pip.py')

@task
def get_rabbitmq():       
    sudo('apt-get install -y rabbitmq-server')
    sudo('rabbitmq-server -detached')
    time.sleep(20)
    sudo('rabbitmq-plugins enable rabbitmq_management')
    sudo('rabbitmq-plugins enable rabbitmq_federation')
    sudo('rabbitmq-plugins enable rabbitmq_federation_management')


@task
def start_rabbit():
    sudo('rabbitmqctl add_user {0} {1}'.format(RABBITMQ_USER, RABBITMQ_PASS))
    sudo('rabbitmqctl set_user_tags {0} administrator'.format(RABBITMQ_USER))
    sudo('rabbitmqctl add_vhost {0}'.format(RABBITMQ_VHOST))
    sudo('sudo rabbitmqctl set_permissions -p {0} {1} ".*" ".*" ".*"'.format('/', 
                                                                           RABBITMQ_USER))
    sudo('sudo rabbitmqctl set_permissions -p {0} {1} ".*" ".*" ".*"'.format(RABBITMQ_VHOST, 
                                                                           RABBITMQ_USER))
                                                                               
    # sudo('rabbitmqctl set_policy federate-me \'^amq\.\' \'{"federation-upstream-set":"all"}\'')
    
 #    hosts = []
#     for name in env.hosts:
#         pass # TODO: use this to set upstreams
    sudo("rabbitmqctl set_policy federate-me '^amq\.' {0} '{1}'".format("localhost", #"{\"uri\" : \"amqp://10.0.1.12\"}"))
    
                                                                          {"uri": "amqp://{0}:{1}@{2}:{3}/{4}".format(RABBITMQ_USER,
                                                                                                                      RABBITMQ_PASS,
                                                                                                                      "67.160.0.6",
                                                                                                                      RABBITMQ_PORT,
                                                                                                                      RABBITMQ_VHOST
                                                                                                                      )}))

@task
def kill_rabbit():
    # sudo('rabbitmqctl delete_user {0}'.format(RABBITMQ_USER))
#     sudo('rabbitmqctl delete_vhost {0}'.format(RABBITMQ_VHOST))
    # sudo('rabbitmqctl stop')
    with lcd('../deploy/'):
        local('kill -9 `cat twistd.pid`')


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
        run('twistd -n node -b {0} -p {1}'.format(ip, port))
        
@task
def create_local_node(port=None):
    with lcd('../deploy/'):
        local('twistd -l deploy_test.log node')
 
def main():
  populate_hosts()
  
  # update system's default application toolset
  # execute(update)

  # Clone the repo and switch to deployment branch
  execute(clone_deploy)

  # Start rabbitmq
  # execute(start_rabbit)

  # Get the repo
  execute(deploy_streams)
  

  # start temporary kademlia node
  execute(create_local_node, RABBITMQ_PORT)

  # get local ipv4 address for bootstrapping (deploying from macbook)
  my_ipv4 = local('ipconfig getifaddr en0', capture=True)

  # start Kademlia network
  execute(start_kademlia, my_ipv4, RABBITMQ_PORT) 
  
  # testing, remove all things
  # execute(kill_rabbit)

if __name__ == '__main__':
  main()
