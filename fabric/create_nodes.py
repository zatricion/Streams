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
def test():
  with settings(prompts={'Are you sure you want to continue connecting (yes/no)? ' : 'yes'}):
    sudo('apt-get install -y git')
    run('git clone git@github.com:zatricion/Streams.git')

def main():
  populate_hosts()
  print env
  r = execute(test)

if __name__ == '__main__':
  main()
