from threading import Thread

import pika
from fastapi import HTTPException
from loguru import logger

from app.core.config import settings
from app.db.init_db import offers_collection, payments_collection


def on_message_store_offer_datawarehouse(channel, method, properties, body):
    """
    Function to store an offer in the MongoDB database.
    """
    body = body.decode()

    # Json
    body = eval(body)

    try:
        # Use o PyMongo para inserir dados de forma síncrona
        offers_collection.insert_one(body)
        logger.info("Offer stored successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# def on_message_purchased_offer(channel, method, properties, body):
#     """
#     Function to update the relevance_score of an offer in the Elasticsearch index.
#     """
#     body = body.decode()

#     # Json
#     body = eval(body)

#     try:
#         payments_collection.insert_one(body)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

def consume_messages():
    """
    Function to consume messages from RabbitMQ.
    """
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=settings.RABBITMQ_HOST,
            port=settings.RABBITMQ_PORT,
            virtual_host=settings.RABBITMQ_VIRTUAL_HOST,
            credentials=pika.PlainCredentials(username=settings.RABBITMQ_USERNAME, password=settings.RABBITMQ_PASSWORD),
        )
    )
    
    channel = connection.channel()

    channel.queue_declare(queue="store_offer_datawarehouse")
    # channel.queue_declare(queue="purchased_offers")


    channel.basic_consume(
        queue="store_offer_datawarehouse",
        on_message_callback=on_message_store_offer_datawarehouse,
        auto_ack=True,
    )

    # channel.basic_consume(
    #     queue="purchased_offers",
    #     on_message_callback=on_message_purchased_offer,
    #     auto_ack=True,
    # )

    channel.start_consuming()