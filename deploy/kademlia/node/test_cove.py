import cove

def callback(ch, method, properties, body):
    print ch, method, properties, cove.unpack(body)
    
cove.send('q2', {'cat': 'dog', 1: 4, 'hello': 9})
cove.receive('q2', callback)
