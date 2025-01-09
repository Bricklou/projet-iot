import pika
import json
import signal
from datetime import datetime


class RabbitMQConsumer:
    def __init__(self, host="localhost", port=5672, user="guest", password="guest"):
        self.credentials = pika.PlainCredentials(user, password)
        self.parameters = pika.ConnectionParameters(
            host=host, port=port, credentials=self.credentials, heartbeat=600
        )
        self.connection: pika.BlockingConnection | None = None
        self.channel = None
        self.should_stop = False

    def connect(self):
        try:
            self.connection = pika.BlockingConnection(self.parameters)
            self.channel = self.connection.channel()
            print("✅ Connecté au serveur RabbitMQ")
            return True
        except Exception as e:
            print(f"❌ Erreur de connexion: {str(e)}")
            return False

    def setup_queue(self, queue_name):
        """Déclare la queue et configure la qualité de service"""
        try:
            self.channel.queue_declare(queue=queue_name, durable=True)
            # Limite à 1 message à la fois par consommateur
            self.channel.basic_qos(prefetch_count=1)
            print(f"✅ Queue '{queue_name}' configurée avec succès")
        except Exception as e:
            print(f"❌ Erreur lors de la configuration de la queue: {str(e)}")

    def process_message(self, ch, method, properties, body):
        """Traitement du message reçu"""
        try:
            message = json.loads(body)
            print(f"\n📨 Message reçu à {datetime.now().isoformat()}:")
            print(json.dumps(message, indent=2))

            # Simulation d'un traitement
            print("⚙️ Traitement du message...")

            # Accusé de réception
            ch.basic_ack(delivery_tag=method.delivery_tag)
            print("✅ Message traité avec succès\n")

        except json.JSONDecodeError:
            print("❌ Message invalide (format JSON incorrect)")
            # On acquitte quand même pour ne pas bloquer la queue
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            print(f"❌ Erreur lors du traitement: {str(e)}")
            # En cas d'erreur, on peut choisir de rejeter le message
            # et le remettre dans la queue pour réessayer plus tard
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    def start_consuming(self, queue_name):
        """Démarre la consommation des messages"""

        def signal_handler(sig, frame):
            """Gestionnaire pour l'arrêt propre du consumer"""
            print("\n🛑 Arrêt du consumer...")
            self.should_stop = True
            if self.channel:
                self.channel.stop_consuming()

        # Configuration du gestionnaire de signal pour Ctrl+C
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        try:
            self.setup_queue(queue_name)

            # Configuration du callback de réception
            self.channel.basic_consume(
                queue=queue_name, on_message_callback=self.process_message
            )

            print(f"🎧 En attente de messages sur la queue '{queue_name}'...")
            print("Appuyez sur Ctrl+C pour arrêter le consumer")

            # Démarrage de la boucle de consommation
            self.channel.start_consuming()

        except Exception as e:
            print(f"❌ Erreur lors de la consommation: {str(e)}")
        finally:
            self.close()

    def close(self):
        """Fermeture propre de la connexion"""
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            print("✅ Connexion fermée")


def main():
    # Initialisation du consumer
    consumer = RabbitMQConsumer(
        host="localhost",  # Modifiez selon votre configuration
        port=5672,
        user="user",
        password="password",
    )

    # Connexion et démarrage de la consommation
    if consumer.connect():
        consumer.start_consuming("iot")


if __name__ == "__main__":
    main()

