import pika
import msgpack
import time

credentials = pika.PlainCredentials('peter', 'rabbit')
parameters = pika.ConnectionParameters(host='localhost',
                                       port=5672,
                                       virtual_host='potter',
                                       credentials=credentials)

class Cove(object):
    def __init__(self):
        self.conn = pika.BlockingConnection(parameters)
        self.channel = self.conn.channel()
        self.queues = []

    def send(self, q_name, message):
        if q_name not in self.queues:
            self.channel.queue_declare(queue=q_name)
            self.queues.append(q_name)
            time.sleep(2)

        self.channel.basic_publish(exchange='',
                                   routing_key=q_name,
                                   body=str(message))
                                   # body=msgpack.packb(message))
        print "send", message, "to", q_name

    def receive(self, q_name, callback):
        print "receive from", q_name
        if q_name not in self.queues:
            self.channel.queue_declare(queue=q_name)
            self.queues.append(q_name)
            time.sleep(2)

        for method_frame, properties, body in self.channel.consume(q_name):
            # Acknowledge the message
            self.channel.basic_ack(method_frame.delivery_tag)
            
            print "received", eval(body), "from", q_name
            
            callback(eval(body))
            # callback(msgpack.unpackb(body, use_list=False))