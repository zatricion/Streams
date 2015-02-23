import jinja2
import os
import shutil
from core.SystemParameters import PROCESS_DIR

cwd = os.getcwd()
templateLoader = jinja2.FileSystemLoader(searchpath=cwd)
templateEnv = jinja2.Environment(loader=templateLoader)

logic_template = templateEnv.get_template('templates/logic.txt')
proc_template = templateEnv.get_template('templates/process.txt')
agent_template = templateEnv.get_template('templates/agent.txt')
file_agent_template = templateEnv.get_template('templates/agent_from_file.txt')
ext_proc_template = templateEnv.get_template('templates/ext_proc.txt')

class GceNetwork(object):
    def __init__(self, name, instance):
        self.name = name
        self.instance = instance
        self.procs = dict()
        self.out_streams_to_procs = dict()
        self.in_streams_to_procs = dict()
        self.net_ext_in_streams = []
        self.net_ext_out_streams = []
    
    def set_ext_procs(self, proc_to_instance_dict):
        self.ext_procs_to_instance = proc_to_instance_dict
        
    def add_process(self, p):
        self.procs[p.name] = p
        
        for stream in p.out_streams_to_agents.keys():
            self.out_streams_to_procs[stream] = p.name
        
        for stream in p.in_streams_to_agents.keys():
            proc_list = self.in_streams_to_procs.setdefault(stream, [])
            proc_list.append(p.name)
    
    def launch(self):
        # set external in and out streams for each process
        for p in self.procs.values():
            p.external_in_streams = p.get_external_in_streams()
            for s in p.external_in_streams:
                if s in self.out_streams_to_procs:
                    correct_out_proc = self.procs[self.out_streams_to_procs[s]]
                    correct_out_proc.external_out_streams.append(s)
                else:
                    # This is an external input stream that is not an output stream
                    # in the network. Therefore it is a network external input stream
                    self.net_ext_in_streams.append(s)
                    
        # set network external output streams
        self.net_ext_out_streams =  list(set(self.out_streams_to_procs.keys()) 
                                        - set(self.in_streams_to_procs.keys()))

        # write process files
        for name, p in self.procs.iteritems():
            if name in self.ext_procs_to_instance:
                p.launch_ext(self.ext_procs_to_instance[name])
            else:
                p.launch()

        # create start_network.py
        logic = logic_template.render(name = self.name,
                                      instance = self.instance,
                                      process_dir = PROCESS_DIR,
                                      processes = self.procs.values(),
                                      in_streams_dict = self.in_streams_to_procs,
                                      out_streams_dict = self.out_streams_to_procs,
                                      external_in_streams = list(set(self.net_ext_in_streams)),
                                      external_out_streams = self.net_ext_out_streams,
                                      external_processes = self.ext_procs_to_instance.keys())
                                      
        with open('start_network.py', 'w') as file:
            file.write(logic)

class GceProcess(object):
    def __init__(self, name):
        self.name = name
        self.agents = []
        self.in_streams_to_agents = dict()
        self.out_streams_to_agents = dict()
        self.external_in_streams = []
        self.external_out_streams = []

    def add_agent(self, agent):
        self.agents.append(agent)
        
        for stream in agent.in_streams:
            self.in_streams_to_agents[stream] = agent.name

        for stream in agent.out_streams:
            self.out_streams_to_agents[stream] = agent.name
    
    def get_internal_streams(self):
        # list of streams inside the process
        return list(set(self.in_streams_to_agents.keys()) 
                     & set(self.out_streams_to_agents.keys()))

    def get_external_in_streams(self):
        # list of in_streams entering the process
        return list(set(self.in_streams_to_agents.keys()) 
                     - set(self.out_streams_to_agents.keys()))
    
    def get_unused_out_streams(self):
        # list of out_streams not used inside the process
        return list(set(self.out_streams_to_agents.keys()) 
                     - set(self.in_streams_to_agents.keys()))
    
    def launch_ext(self, instance):
        # launch a phantom process that forwards all input to the taskqueue
        self.external_out_streams.extend(self.get_unused_out_streams())
        proc = ext_proc_template.render(name=self.name,
                                        instance=instance,
                                        external_in_streams = list(set(self.external_in_streams)),
                                        external_out_streams = list(set(self.external_out_streams)))
        with open(PROCESS_DIR + '/' + self.name + '.py', 'w') as file:
            file.write(proc)

    def launch(self):
        # Get code from files (should consist of a function of the same name as the file)
        agents = []
        for a in self.agents:  
            if a.file:
                with open(a.file, 'r') as f:
                    agents.append(file_agent_template.render(name = a.file.strip('.py'),
                                                             parameters = a.parameters,
                                                             in_streams = a.in_streams,
                                                             out_streams = a.out_streams,
                                                             agent = f.read()))
            else:
                agents.append(agent_template.render(name = a.name,
                                                    in_streams = a.in_streams,
                                                    out_streams = a.out_streams,
                                                    agent_type = a.agent_type,
                                                    function = a.function,
                                                    parameters = a.parameters,
                                                    imports = a.imports))

        stream_names = self.get_internal_streams()
        self.external_out_streams.extend(self.get_unused_out_streams())
        proc = proc_template.render(name = self.name,
                                    agents = agents,
                                    streams = stream_names,
                                    external_in_streams = list(set(self.external_in_streams)),
                                    external_out_streams = list(set(self.external_out_streams)))
        print self.name
        with open(PROCESS_DIR + '/' + self.name + '.py', 'w') as file:
            file.write(proc)

class GceAgent(object):
    def __init__(self, name, 
                       file=None,
                       agent_type=None,
                       function=None,
                       imports=None,
                       parameters=None):
        self.name = name
        self.file = file
        self.agent_type = agent_type
        self.function = function
        self.imports = imports
        self.parameters = parameters
        self.in_streams = []
        self.out_streams = []
        
    def add_input(self, stream):
        self.in_streams.append(stream)
    
    def add_output(self, stream):
        self.out_streams.append(stream)
