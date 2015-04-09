
from fabric.api import *
import fabric.contrib.files as fabfiles

HOSTS = 'hosts_ipv4.txt'
env.forward_agent = True
env.key_filename = '~/.ssh/streams_deploy'
env.abort_on_prompts = True

def populate_hosts():
  for line in open(HOSTS, 'r'):
    if line.strip() and not line.startswith('#'):
      host, password = line.split()
      env.hosts.append(host)
      env.passwords[host] = password

@task
def clone_deploy():
  with settings(prompts={'Are you sure you want to continue connecting (yes/no)? ' : 'yes'}):
    sudo('apt-get install -y git')
    if not fabfiles.exists('Streams'):
      run('git clone git@github.com:zatricion/Streams.git')
      with cd('Streams'):
        run('git checkout deployment')
    else:
      with cd('Streams'):
        run('git fetch --all')
        run('git reset --hard origin/deployment')

@task
def start_kademlia(ip, port=None):
  with cd('Streams/kademlia'):
    run('twistd -n node -b {0} -p {1}'.format(ip, port))

def main():
  populate_hosts()

  # Clone the repo and switch to deployment branch
  execute(clone_deploy)

  # get local ipv6 address for bootstrapping (deploying from macbook)
  my_ipv6 = local('ifconfig | grep inet6 | grep temporary', capture=True).split()[1]
  
  # start Kademlia network
  execute(start_kademlia, my_ipv6, 5768) 

if __name__ == '__main__':
  main()
