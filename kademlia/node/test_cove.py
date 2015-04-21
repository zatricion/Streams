from cove import Cove

def callback(ch, method, properties, body):
    print ch, method, properties, cove.unpack(body)
    
cove = Cove(['q1', 'q2', 'q3'])
cove.send('q2', {'cat': 'dog', 1: 4, 'hello': 9})
cove.receive('q2', callback)
