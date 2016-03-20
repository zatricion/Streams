import time
from fabric.api import *
import fabric.contrib.files as fabfiles

RABBITMQ_USER = 'peter'
RABBITMQ_PASS = 'rabbit'
RABBITMQ_VHOST = 'potter'
RABBITMQ_PORT = 7001

HOSTS = 'hosts_ipv4.txt'
env.forward_agent = True
env.key_filename = '~/.ssh/id_rsa'
env.abort_on_prompts = True
env.hostnames = {}
env.addrs = {}
env.warn_only=True

def populate_hosts():
    for line in open(HOSTS, 'r'):
        if line.strip() and not line.startswith('#'):
            name, host, password = line.split()
            env.hosts.append(host)
            # env.passwords[host+':22'] = password
            env.hostnames[host.split('@')[1]] = name
            env.addrs[name] = host
         
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
        
        # get python development tools
        sudo('apt-get install -y python-dev')
        
        # get gcc
        sudo('apt-get install -y gcc')

@task
def set_rabbit():       
    sudo('apt-get install -y --force-yes rabbitmq-server')
    sudo('rabbitmq-server -detached')
    time.sleep(20)
    sudo('rabbitmqctl start_app')
    sudo('rabbitmq-plugins enable rabbitmq_management')
    sudo('rabbitmq-plugins enable rabbitmq_federation')
    sudo('rabbitmq-plugins enable rabbitmq_federation_management')
    sudo('rabbitmqctl add_user {0} {1}'.format(RABBITMQ_USER, RABBITMQ_PASS))
    sudo('rabbitmqctl set_user_tags {0} administrator'.format(RABBITMQ_USER))
    sudo('rabbitmqctl add_vhost {0}'.format(RABBITMQ_VHOST))
    sudo('sudo rabbitmqctl set_permissions -p {0} {1} ".*" ".*" ".*"'.format('/', 
                                                                           RABBITMQ_USER))
    sudo('sudo rabbitmqctl set_permissions -p {0} {1} ".*" ".*" ".*"'.format(RABBITMQ_VHOST, 
                                                                           RABBITMQ_USER))

@task
def federate_rabbit():
    sudo("rabbitmqctl set_policy -p {0} --apply-to queues federate-me '.+' '{{\"federation-upstream-set\":\"all\"}}'".format(RABBITMQ_VHOST))
    
    for host in env.hosts:
        ip_addr = host.split('@')[1]
        if ip_addr == env.host: continue # don't add yourself as an upstream
        
        upstream =  '{{"uri": "amqp://{0}:{1}@{2}/{3}"}}'.format(RABBITMQ_USER,
                                                                   RABBITMQ_PASS,
                                                                   ip_addr,
                                                                   RABBITMQ_VHOST
                                                                   )
        sudo("rabbitmqctl set_parameter -p {0} federation-upstream {1} '{2}' ".format(RABBITMQ_VHOST, env.hostnames[ip_addr], upstream))

@task
def kill_rabbit():
    sudo('rabbitmqctl delete_user {0}'.format(RABBITMQ_USER))
    sudo('rabbitmqctl delete_vhost {0}'.format(RABBITMQ_VHOST))
    with lcd('../deploy/'):
        local('kill -9 `cat twistd.pid`')

 
def main():
  # update system's default application toolset
  execute(update)

  # Clone the repo and switch to deployment branch
  execute(clone_deploy)

  # Start rabbitmq
  execute(set_rabbit)
  execute(federate_rabbit)

if __name__ == '__main__':
  populate_hosts()
  main()
