import pika
import msgpack

credentials = pika.PlainCredentials('peter', 'rabbit')
parameters = pika.ConnectionParameters(host='localhost',
                                       port=5672,
                                       virtual_host='potter',
                                       credentials=credentials)

class Cove(object):
    def __init__(self):
        self.conn = pika.BlockingConnection(parameters)
        self.channel = self.conn.channel()

    def send(self, q_name, message):
        self.channel.queue_declare(queue=q_name)

        self.channel.basic_publish(exchange='',
                                   routing_key=q_name,
                                   body=str(message))
                                   # body=msgpack.packb(message))
        print "send", message, "to", q_name

    def receive(self, q_name, callback):
        print "receive from", q_name
        self.channel.queue_declare(queue=q_name)

        for method_frame, properties, body in self.channel.consume(q_name):
            # Acknowledge the message
            self.channel.basic_ack(method_frame.delivery_tag)
            
            print "received", eval(body), "from", q_name
            
            callback(eval(body))
            # callback(msgpack.unpackb(body, use_list=False))