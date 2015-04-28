import pika
import msgpack

conn = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = conn.channel()

def send(q_name, message):
    channel.queue_declare(queue=q_name)
    channel.basic_publish(exchange='',
                              routing_key=q_name,
                              body=msgpack.packb(message))

def receive(q_name, callback):
    channel.queue_declare(queue=q_name)    
    channel.basic_consume(callback, queue=q_name, no_ack=False)
    channel.start_consuming()

def unpack(message):
    return msgpack.unpackb(message, use_list=False)
