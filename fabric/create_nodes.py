from fabric.api import *
import fabric.contrib.files as fabfiles

RABBITMQ_USER = 'peter'
RABBITMQ_PASS = 'rabbit'
RABBITMQ_VHOST = 'potter'

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
            env.passwords[host] = password
            env.hostnames[host.split('@')[1]] = name
         
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

        # get rabbitmq
        sudo('apt-get install -y rabbitmq-server')
        sudo('rabbitmq-plugins enable rabbitmq_federation')
        sudo('rabbitmq-plugins enable rabbitmq_federation_management')

@task
def start_rabbit():
    if RABBITMQ_USER not in sudo('rabbitmqctl list_users').stdout:
        sudo('rabbitmqctl add_user {0} {1}'.format(RABBITMQ_USER, RABBITMQ_PASS))
        sudo('rabbitmqctl add_vhost {0}'.format(RABBITMQ_VHOST))
        sudo('sudo rabbitmqctl set_permissions -p {0} {1} ".*" ".*" ".*"'.format(RABBITMQ_VHOST, 
                                                                                 RABBITMQ_USER))
                                                                                 
        # sudo('rabbitmqctl set_policy federate-me \'^amq\.\' \'{"federation-upstream-set":"all"}\'')
        sudo('rabbitmq-server')

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
    with cd('Streams/kademlia'):
        run('twistd -n node -b {0} -p {1}'.format(ip, port))
 
def main():
  populate_hosts()
  
  # Clone the repo and switch to deployment branch
  # execute(clone_deploy)
  
  # Start rabbitmq
  execute(start_rabbit)
  
  # Get the repo
  execute(deploy_streams)

  # get local ipv4 address for bootstrapping (deploying from macbook)
  my_ipv4 = local('ipconfig getifaddr en0', capture=True)
  
  # start Kademlia network
  execute(start_kademlia, my_ipv4, 7000) 

if __name__ == '__main__':
  main()
