
from fabric.api import *
import fabric.contrib.files as fabfiles

HOSTS = 'hosts.txt'
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
        run('git pull')

@task
def start_kademlia():
  pass

def main():
  populate_hosts()

  # Clone the repo and switch to deployment branch
  #execute(clone_deploy)

  # get local ipv6 address for bootstrapping (deploying from macbook)
  my_ipv6 = local('ifconfig | grep inet6 | grep temporary', capture=True).split()[1]
  
  # start Kademlia network
  execute(start_kademlia) 

if __name__ == '__main__':
  main()
