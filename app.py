import pika
import ssl
from transformers import pipeline
import torch


device = 0 if torch.cuda.is_available() else -1

def model_translator_es_en():
    return pipeline("translation", model="Helsinki-NLP/opus-mt-es-en", device=device)

def model_translator_en_es():
    return pipeline("translation", model="Helsinki-NLP/opus-mt-en-es", device=device)

def model_corrector():
    return pipeline('text2text-generation', model='facebook/bart-large', device=device)

translator_es_en = model_translator_es_en()
translator_en_es = model_translator_en_es()
corrector = model_corrector()

def get_rabbit_connection():
    rabbitmq_host = 'b-4ebf1ed0-96b6-44cd-a463-df7ca073c483.mq.us-east-2.amazonaws.com'
    rabbitmq_port = 5671
    rabbitmq_user = 'admin'
    rabbitmq_password = 'adminadminadmin'
    virtual_host = '/'

    credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_password)

    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = True
    ssl_context.verify_mode = ssl.CERT_REQUIRED

    ssl_options = pika.SSLOptions(ssl_context, rabbitmq_host)

    parameters = pika.ConnectionParameters(
        host=rabbitmq_host,
        port=rabbitmq_port,
        virtual_host=virtual_host,
        credentials=credentials,
        ssl_options=ssl_options
    )
    return pika.BlockingConnection(parameters)

def send_message(response, correlation_id):
    connection = get_rabbit_connection()
    channel = connection.channel()
    channel.queue_declare(queue='create_description_response.queue', durable=True)

    payload = response
    message_properties = pika.BasicProperties(
        correlation_id=correlation_id
    )
    channel.basic_publish(
        exchange='',
        routing_key='create_description_response.queue',
        properties=message_properties,
        body=payload.encode()
    )
    connection.close()

def on_message(ch, method, properties, body):
    input_text = body.decode()
    session_uuid = properties.correlation_id

    prompt_en = translator_es_en(input_text)[0]['translation_text']

    corrected_text_en = corrector(prompt_en, max_length=512, num_return_sequences=1)[0]['generated_text']

    corrected_text_es = translator_en_es(corrected_text_en)[0]['translation_text']

    send_message(corrected_text_es, session_uuid)

    ch.basic_ack(delivery_tag=method.delivery_tag)

def start_consumer():
    connection = get_rabbit_connection()
    channel = connection.channel()

    channel.queue_declare(queue='create_description_request.queue', durable=True)
    channel.queue_declare(queue='create_description_response.queue', durable=True)

    channel.basic_consume(queue='create_description_request.queue', on_message_callback=on_message)

    print('Esperando mensajes. Para salir presiona CTRL+C')
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print('Consumo interrumpido por el usuario.')
    finally:
        connection.close()

if __name__ == "__main__":
    start_consumer()
