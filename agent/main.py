import pika
import json
import time
from datetime import datetime

class RabbitMQClient:
    def __init__(self, host='localhost', port=5672, user='guest', password='guest'):
        self.credentials = pika.PlainCredentials(user, password)
        self.parameters = pika.ConnectionParameters(
            host=host,
            port=port,
            credentials=self.credentials,
            heartbeat=600
        )
        self.connection = None
        self.channel = None

    def connect(self):
        try:
            self.connection = pika.BlockingConnection(self.parameters)
            self.channel = self.connection.channel()
            print("✅ Connecté au serveur RabbitMQ")
            return True
        except Exception as e:
            print(f"❌ Erreur de connexion: {str(e)}")
            return False

    def create_queue(self, queue_name):
        try:
            self.channel.queue_declare(queue=queue_name, durable=True)
            print(f"✅ Queue '{queue_name}' créée avec succès")
        except Exception as e:
            print(f"❌ Erreur lors de la création de la queue: {str(e)}")

    def send_message(self, queue_name, message):
        try:
            self.channel.basic_publish(
                exchange='',
                routing_key=queue_name,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Message persistant
                    content_type='application/json'
                )
            )
            print(f"✅ Message envoyé: {message}")
        except Exception as e:
            print(f"❌ Erreur lors de l'envoi du message: {str(e)}")

    def close(self):
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            print("✅ Connexion fermée")

def generate_test_message():
    return {
        "id": int(time.time()),
        "timestamp": datetime.now().isoformat(),
        "content": "Message de test",
        "status": "pending"
    }

def main():
    # Initialisation du client
    client = RabbitMQClient(
        host='localhost',  # Modifiez selon votre configuration
        port=5672,
        user='user',
        password='password'
    )

    # Connexion au serveur
    if client.connect():
        queue_name = 'iot'
        
        # Création de la queue
        client.create_queue(queue_name)
        
        # Envoi de 10 messages de test
        for i in range(10):
            message = generate_test_message()
            client.send_message(queue_name, message)
            time.sleep(1)  # Attente d'une seconde entre chaque message
        
        # Fermeture de la connexion
        client.close()

if __name__ == "__main__":
    main()
