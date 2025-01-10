import csv
import json
import os
import paho.mqtt.client as mqtt
import time


class EventsMqttAgent:
    NEEDED_COLUMNS = [
        "detectiontime",
        "eventposition_latitude",
        "eventposition_longitude",
        "referenceposition_longitude",
    ]
    LINE_SKIP_AT_START_OF_FILE = 1

    def __init__(self, source_file: str, mqtt_config: dict[str, str]) -> None:
        # Check if fsource file exists
        if not os.path.exists(source_file):
            raise FileNotFoundError(f"File {source_file} does not exist")

        self.source_file = source_file

        # Check the mqtt data are valid
        if not all(key in mqtt_config for key in ("broker_ip", "broker_port", "topic")):
            raise ValueError("Invalid MQTT data")

        self.mqtt_config = mqtt_config

        self._connect()

    def _connect(self) -> None:
        self.mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.mqtt_client.on_connect = self._on_connect

        print(
            f"Connecting to {self.mqtt_config['broker_ip']}:{self.mqtt_config['broker_port']} with user \"{self.mqtt_config["user"]}\" and password \"{self.mqtt_config["password"]}\""
        )
        self.mqtt_client.username_pw_set(
            self.mqtt_config["user"], self.mqtt_config["password"]
        )
        self.mqtt_client.connect(
            self.mqtt_config["broker_ip"], int(self.mqtt_config["broker_port"]), 60
        )

        self.mqtt_client.loop_start()

    def _on_connect(self, _client, _userdata, _flags, reason_code, _properties) -> None:
        print(f"Connected with result code {reason_code}")
        self.mqtt_client.subscribe(self.mqtt_config["topic"])

    def send_data(self) -> None:
        # Read data from the source file and send it
        with open(self.source_file, mode="r") as file:
            reader = csv.reader(file)
            line = 0
            for raw in reader:
                # Skip the header line
                if line == 0:
                    line += 1
                    continue

                self._send_row(raw)
                time.sleep(1)

                # Increment the count
                line += 1

        self.mqtt_client.disconnect()

    def _send_row(self, raw: list[str]) -> None:
        row = self._format_row(raw)
        row = json.dumps(row)

        TOPIC = self.mqtt_config["topic"]
        request = self.mqtt_client.publish(TOPIC, row, qos=1)
        request.wait_for_publish()

    def _format_row(self, raw: list[str]) -> dict[str, str | float]:
        return {
            "timestamp": raw[12],
            "event": float(raw[29]),
            "latitude": float(raw[16]),
            "longitude": float(raw[17]),
        }


def main():
    # Extract environment variables
    source_file = os.getenv("SOURCE_FILE")
    if not source_file:
        raise ValueError("SOURCE_FILE environment variable is required")

    port = os.getenv("MQTT_BROKER_PORT")
    if not port:
        raise ValueError("MQTT_BROKER_PORT environment variable is required")
    port = int(port)

    mqtt = {
        "broker_ip": os.getenv("MQTT_BROKER_IP"),
        "broker_port": port,
        "topic": os.getenv("MQTT_TOPIC", "traffic/events"),
        "user": os.getenv("MQTT_USER"),
        "password": os.getenv("MQTT_PASSWORD"),
    }

    agent = EventsMqttAgent(source_file, mqtt)
    agent.send_data()


if __name__ == "__main__":
    main()
