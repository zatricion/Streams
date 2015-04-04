from fabric.api import *

HOSTS = 'hosts.txt'

def populate_hosts():
  for line in open(HOSTS, 'r'):
    if line.strip() and not line.startswith('#'):
      host, password = line.split()
      env.hosts.append(host)
      env.passwords[host] = password

@task
def test():
  run('touch supercalifragilistic.txt')

def main():
  populate_hosts()
  r = execute(test) 

if __name__ == '__main__':
  main()
