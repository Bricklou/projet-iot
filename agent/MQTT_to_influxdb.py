import os
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import paho.mqtt.client as mqtt
import json
from datetime import datetime

# DEBUG -- print data instead of sending data via MQTT
DEBUG = True


class MQTTtoInfluxBridge:
    def __init__(
        self,
        mqtt_broker,
        mqtt_port,
        mqtt_user,
        mqtt_password,
        influx_url,
        influx_token,
        influx_org,
        influx_bucket,
    ):
        # MQTT setup
        self.mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.mqtt_broker = mqtt_broker
        self.mqtt_port = mqtt_port
        self.mqtt_user = mqtt_user
        self.mqtt_password = mqtt_password

        # Set up MQTT callbacks
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message

        # InfluxDB setup
        self.influx_client = InfluxDBClient(
            url=influx_url, token=influx_token, org=influx_org
        )
        self.write_api = self.influx_client.write_api(write_options=SYNCHRONOUS)
        self.influx_bucket = influx_bucket
        self.influx_org = influx_org

    def on_connect(self, _client, _userdata, _flags, reason_code, _properties) -> None:
        """Callback when connected to MQTT broker."""
        if reason_code == 0:
            print(f"Connected to MQTT broker at {self.mqtt_broker}")

            # Subscribe to topic(s)
            self.mqtt_client.subscribe("traffic/#")  # Subscribe to all sensor topics
        else:
            print(f"Connection failed with code {reason_code}")

    def on_message(self, client, userdata, msg):
        """Callback when message is received."""
        try:
            # Parse JSON message
            payload = json.loads(msg.payload.decode())
            print(f"Received payload: {payload}")

            # Safely convert string values to float
            try:
                speed = float(payload.get("speed", "-1"))
                event = float(payload.get("event", "-1"))
                lat = float(payload.get("latitude", "-1"))
                long = float(payload.get("longitude", "-1"))

                # Create InfluxDB point with converted values
                point = None
                if not speed == -1:
                    point = (
                        Point("info")
                        .tag("info", "info")
                        .field("speed", speed)
                        .field("lat", lat)
                        .field("long", long)
                    )
                else:
                    point = (
                        Point("event")
                        .tag("event", "event")
                        .field("event", event)
                        .field("lat", lat)
                        .field("long", long)
                    )

                # Write to InfluxDB
                self.write_api.write(
                    bucket=self.influx_bucket, org=self.influx_org, record=point
                )

                print(f"Data written to InfluxDB: {payload}")

            except ValueError as ve:
                print(f"Error converting string to float: {ve}")
                print(
                    f"Payload values: speed={payload.get('speed')}, lat={payload.get('latitude')}, long={payload.get('longitude')}"
                )

        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            print(msg.payload)
        except Exception as e:
            print(f"Error processing message: {e}")
            print(msg.payload)

    def start(self):
        """Start the bridge."""
        try:
            # Connect to MQTT broker
            self.mqtt_client.username_pw_set(self.mqtt_user, self.mqtt_password)
            self.mqtt_client.connect(self.mqtt_broker, self.mqtt_port)

            # Start the MQTT loop
            print("Starting MQTT to InfluxDB bridge...")
            self.mqtt_client.loop_forever()

        except Exception as e:
            print(f"Error starting bridge: {e}")
            self.stop()

    def stop(self):
        """Stop the bridge."""
        self.mqtt_client.disconnect()
        self.influx_client.close()
        print("Bridge stopped")


# Example usage
if __name__ == "__main__":
    BROKER_IP = os.getenv("MQTT_BROKER_IP")
    BROKER_PORT = os.getenv("MQTT_BROKER_PORT")
    # Check if the port is an integer
    if not BROKER_PORT or not BROKER_PORT.isdigit():
        raise ValueError("MQTT_BROKER_PORT must be a valid integer")
    BROKER_PORT = int(BROKER_PORT)

    USER = os.getenv("MQTT_USER")
    PASSWORD = os.getenv("MQTT_PASSWORD")

    INFLUXDB_URL = os.getenv("INFLUXDB_URL")
    INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN")
    INFLUXDB_ORG = os.getenv("INFLUXDB_ORG")
    INFLUXDB_BUCKET = os.getenv("INFLUXDB_BUCKET")

    # Create and start the bridge
    bridge = MQTTtoInfluxBridge(
        BROKER_IP,
        BROKER_PORT,
        USER,
        PASSWORD,
        INFLUXDB_URL,
        INFLUXDB_TOKEN,
        INFLUXDB_ORG,
        INFLUXDB_BUCKET,
    )

    try:
        bridge.start()
    except KeyboardInterrupt:
        bridge.stop()
