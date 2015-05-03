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
    channel.queue_bind(exchange='amq.direct',
                       queue=q_name,
                       routing_key=q_name)
                       
    channel.basic_publish(exchange='amq.direct',
                          routing_key=q_name,
                          body=msgpack.packb(message))
    # debug
    channel.basic_publish(exchange='',
                              routing_key=q_name,
                              body=str(message))

def receive(q_name, callback):
    channel.queue_declare(queue=q_name)
    channel.queue_bind(exchange='amq.direct',
                       queue=q_name,
                       routing_key=q_name)

    channel.basic_consume(callback, queue=q_name, no_ack=False)
    channel.start_consuming()

def unpack(message):
    return msgpack.unpackb(message, use_list=False)
