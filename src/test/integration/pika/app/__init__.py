import pika
from fastapi import FastAPI, Request

app = FastAPI()
test_message = "Hello World!"


@app.get("/")
async def root():
    return {"message": "Hello FastAPI!"}


def on_message(channel, method_frame, header_frame, body):
    decoded_body = str(body, "utf-8")
    print(f"message received: method_frame: {method_frame}, body: {decoded_body}")
    channel.basic_ack(delivery_tag=method_frame.delivery_tag)
    channel.stop_consuming()


@app.post("/invoke-pika-consumer")
async def invoke_pika_consumer(request: Request):
    request_body = await request.json()
    connection_params = request_body["connection_params"]
    print(f"connection_params: {connection_params}")
    topic = request_body["topic"]
    print(f"topic: {topic}")
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=connection_params["host"], port=connection_params["port"]
        )
    )
    print("consumer connection created")
    channel = connection.channel()
    print(f"consumer connection.is_open: {connection.is_open}")

    queue_status = channel.queue_declare(queue=topic)
    # WARNING: this works, but the value of message_count is only accurate as
    # of the last time the queue was declared. The only methods to determine
    # the number of messages in a queue don't appear to work,
    # see https://stackoverflow.com/a/13629296/2860309
    assert queue_status.method.message_count > 0

    channel.basic_consume(topic, on_message)
    try:
        channel.start_consuming()
    except Exception as e:
        print(f"Exception while consuming messages: {e}")
        channel.stop_consuming()
    return {"status": "ok"}


@app.post("/invoke-pika-producer")
async def invoke_pika_producer(request: Request):
    request_body = await request.json()
    connection_params = request_body["connection_params"]
    print(f"connection_params: {connection_params}")
    topic = request_body["topic"]
    print(f"topic: {topic}")
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=connection_params["host"], port=connection_params["port"]
        )
    )
    print("producer connection created")
    channel = connection.channel()
    print(f"producer connection.is_open: {connection.is_open}")
    channel.queue_declare(queue=topic)
    channel.basic_publish(exchange="", routing_key=topic, body=test_message)

    connection.close()

    return {"status": "ok"}
