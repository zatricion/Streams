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

    def receive(self, q_name, callback):
        channel.queue_declare(queue=q_name)

        # TODO: find a better way than unbind,bind
        channel.queue_unbind(exchange='amq.direct',
                             queue=q_name,
                             routing_key=q_name)
        channel.queue_bind(exchange='amq.direct',
                           queue=q_name,
                           routing_key=q_name)

        for method_frame, properties, body in channel.consume(q_name):
            # Display the message parts
            print method_frame
            print properties
            print body

            # Acknowledge the message
            channel.basic_ack(method_frame.delivery_tag)

            callback(msgpack.unpackb(message, use_list=False))