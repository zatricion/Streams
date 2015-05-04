import pika
import msgpack

credentials = pika.PlainCredentials('peter', 'rabbit')
conn = pika.BlockingConnection(pika.ConnectionParameters(host='localhost',
                                                         port=5672,
                                                         virtual_host='potter',
                                                         credentials=credentials))
channel = conn.channel()

def send(q_name, message):
    channel.queue_declare(queue=q_name)
 
    # TODO: find a better way than unbind,bind
    channel.queue_unbind(exchange='amq.direct',
                         queue=q_name,
                         routing_key=q_name)

    channel.queue_bind(exchange='amq.direct',
                       queue=q_name,
                       routing_key=q_name)
                       
    channel.basic_publish(exchange='amq.direct',
                          routing_key=q_name,
                          body=msgpack.packb(message))

def receive(q_name, callback):
    channel.queue_declare(queue=q_name)
    
    # TODO: find a better way than unbind,bind
    channel.queue_unbind(exchange='amq.direct',
                         queue=q_name,
                         routing_key=q_name)
    channel.queue_bind(exchange='amq.direct',
                       queue=q_name,
                       routing_key=q_name)

    while True:
        result = channel.basic_get(queue=q_name, no_ack=False)
        if not result:
            break
        
        callback(self.unpack(result['body']))
        channel.basic_ack(result['method']['delivery_tag'])

def unpack(message):
    return msgpack.unpackb(message, use_list=False)
