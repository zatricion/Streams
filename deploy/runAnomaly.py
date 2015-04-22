import sys
import json
from pyparsing import *
from GceAnomaly import GceNetwork, GceProcess, GceAgent
from core.SystemParameters import PROCESS_DIR
import os, errno

"""
agent Name {
    process: process_name
    type: scikit
    function: scikit_predict
    imports {
        from sklearn.tree import DecisionTreeClassifier
    }
    parameters {
        criterion: "gini"
        max_features: 5
    }
    input_streams {
        stream_one
        stream_two
    }
    output_streams {
        stream_three
    }
    
    // If this is specified, no algorithm is used
    file_name: full_path_to_logic.py
}
"""

### Grammar ###
anomalyObject = Forward()
agentObject = Forward()

valids = printables.replace("{|}", "").replace(":", "")

openB = Suppress('{')
closeB = Suppress('}')
colon = Suppress(':')
agent = Suppress(CaselessKeyword('agent')) + Word(valids)

param = Group(Word(valids) + colon + restOfLine)
paramList = Dict(delimitedList(param, delim = LineEnd()))
importList = Group(delimitedList(Combine(Group(Word(valids) + restOfLine)), delim = LineEnd()))
itemList = Group(delimitedList(Word(valids), delim = LineEnd()))

process = Group(Keyword('process') + colon + Word(valids))
agent_type = Group(Keyword('type') + colon + Word(valids))
function = Group(Keyword('function') + colon + Word(valids))
file = Group(Keyword('file_name') + colon + Word(valids))

imports = Group(Keyword('imports') + openB + Optional(importList) + closeB)
parameters = Group(Keyword('parameters') + openB + Optional(paramList) + closeB)
input = Group(Keyword('input_streams') + openB + Optional(itemList) + closeB)
output = Group(Keyword('output_streams') + openB + Optional(itemList) + closeB)

agentObject << Group(agent + openB + 
                        Dict(process) +
                        (Dict(file) ^ (Dict(agent_type) + Dict(function) + Optional(Dict(imports)))) +
                        Optional(Dict(parameters)) +
                        Dict(input) + 
                        Dict(output)  + closeB)

anomalyObject << Dict(OneOrMore(agentObject))

### Parse ###
def main():
    this_instance = sys.argv[3]
    instance_config = sys.argv[2]
    with open(instance_config, 'r') as file:
        instance_to_proc_dict = json.loads(file.read())
        proc_to_instance_dict = {}
        for k, v in instance_to_proc_dict.items():
            for proc in v:
                if proc_to_instance_dict.get(proc) != None:
                    raise Exception("External configuration file assigns same process to multiple machines")
                if k != this_instance:
                    proc_to_instance_dict[proc] = k

    filename = sys.argv[1]
    # Import text file in anomaly format (.any) as string for parsing and parse it
    with open(filename, 'r') as file:
        parse(file.read(), filename, proc_to_instance_dict, this_instance)

def parse(file, filename, proc_to_instance_dict, this_instance):
    network = anomalyObject.parseString(file).asDict()

    # Create gce_network
    gce_network = GceNetwork(filename.strip('.any'), this_instance)
    processes = {}
    for agent_name, spec in network.iteritems():
        # get parameters
        params = None
        if 'parameters' in spec:
            params = spec['parameters'].asDict()
            
        # create module
        if 'file_name' in spec:
            agent = GceAgent(name=agent_name,
                             file=spec['file_name'],
                             parameters=params)
        else:
            imports = None
            if 'imports' in spec:
                imports = spec['imports']
            agent = GceAgent(name=agent_name,
                             agent_type=spec['type'],
                             function=spec['function'],
                             imports=imports,
                             parameters=params)
        # input streams
        for in_stream in spec['input_streams']:
            agent.add_input(in_stream)
            
        # output streams
        for out_stream in spec['output_streams']:
            agent.add_output(out_stream)
        
        # add agent to process
        proc_name = spec['process']
        if proc_name in processes:
            processes[proc_name].add_agent(agent)
        else:
            proc = GceProcess(proc_name)
            proc.add_agent(agent)
            processes[proc_name] = proc
    
    # add processes to network
    for p in processes.values():
        gce_network.add_process(p)
    
    # set the external process dict
    gce_network.set_ext_procs(proc_to_instance_dict)
    
    # Launch gce network
    gce_network.launch()

def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else: raise

if __name__ == '__main__':
    mkdir_p(PROCESS_DIR)
    open(PROCESS_DIR + '/__init__.py', 'a').close()
    main()
