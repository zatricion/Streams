import pika
import msgpack

class Cove():
    def __init__(self, queues):
        self.conn = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        self.channel = self.conn.channel()
        self.queues = queues

    def send(self, q_name, message):
        self.channel.queue_declare(queue=q_name)
        self.channel.basic_publish(exchange='',
                                  routing_key=q_name,
                                  body=msgpack.packb(message))
  
    def receive(self, q_name, callback):
        self.channel.queue_declare(queue=q_name)    
        self.channel.basic_consume(callback, queue=q_name, no_ack=False)
        self.channel.start_consuming()

    def unpack(self, message):
        return msgpack.unpackb(message)