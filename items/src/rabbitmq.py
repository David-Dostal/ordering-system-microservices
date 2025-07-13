import pika

conn_params = pika.ConnectionParameters(
    host='rabbitmq',
    credentials=pika.PlainCredentials('user', 'secret')
)

def publish(msg: str):
    conn = pika.BlockingConnection(conn_params)
    channel = conn.channel()
    channel.basic_publish(
        exchange='',
        routing_key='orders',
        body=msg
    )
    conn.close()