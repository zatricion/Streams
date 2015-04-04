from fabric.api import *

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
    run('git clone git@github.com:zatricion/Streams.git')
    run('git checkout deployment')

def main():
  populate_hosts()

  # Clone the repo and switch to deployment branch
  execute(clone_deploy)


if __name__ == '__main__':
  main()
