from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import paho.mqtt.client as mqtt
import json
from datetime import datetime

# MQTT parameters
BROKER_IP = "localhost"
BROKER_PORT = 1883
KEEP_ALIVE = 60
TOPIC = "traffic/info"
USER = "user"
PASSWORD = "password"

# InfluxDB parameters
INFLUXDB_URL = "http://localhost:8086"
INFLUXDB_TOKEN = "lkvv1hrjdcCBqx5iNq9qY_TNJNNf8_e_C93iCp6pU7PgBdUnZqR235nybYu2a_CkKLEhTmSMy2TNkUvJhMGLKA=="
INFLUXDB_ORG = "LMO"
INFLUXDB_BUCKET = "IoT"

# DEBUG -- print data instead of sending data via MQTT
DEBUG = True

class MQTTtoInfluxBridge:
    def __init__(self, mqtt_broker, mqtt_port, mqtt_user, mqtt_password, influx_url, influx_token, influx_org, influx_bucket):
        # MQTT setup
        self.mqtt_client = mqtt.Client()
        self.mqtt_broker = mqtt_broker
        self.mqtt_port = mqtt_port
        self.mqtt_user = mqtt_user
        self.mqtt_password = mqtt_password
        
        # Set up MQTT callbacks
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        
        # InfluxDB setup
        self.influx_client = InfluxDBClient(
            url=influx_url,
            token=influx_token,
            org=influx_org
        )
        self.write_api = self.influx_client.write_api(write_options=SYNCHRONOUS)
        self.influx_bucket = influx_bucket
        self.influx_org = influx_org

    def on_connect(self, client, userdata, flags, rc):
        """Callback when connected to MQTT broker."""
        if rc == 0:
            print(f"Connected to MQTT broker at {self.mqtt_broker}")
            # Subscribe to topic(s)
            self.mqtt_client.subscribe("traffic/info")  # Subscribe to all sensor topics
        else:
            print(f"Connection failed with code {rc}")

    def on_message(self, client, userdata, msg):
        """Callback when message is received."""
        try:
            # Parse JSON message
            payload = json.loads(msg.payload.decode())
            print(f"Received payload: {payload}")
            
            # Safely convert string values to float
            try:
                speed = float(payload.get("speed", "0"))
                lat = float(payload.get("latitude", "0"))
                long = float(payload.get("longitude", "0"))
                
                # Create InfluxDB point with converted values
                point = (
                    Point("info")
                    .field("speed", speed)
                    .field("lat", lat)
                    .field("long", long)
                    .time(datetime.now())
                )
                
                # Write to InfluxDB
                self.write_api.write(
                    bucket=self.influx_bucket,
                    org=self.influx_org,
                    record=point
                )
                
                print(f"Data written to InfluxDB: {payload}")
                
            except ValueError as ve:
                print(f"Error converting string to float: {ve}")
                print(f"Payload values: speed={payload.get('speed')}, lat={payload.get('latitude')}, long={payload.get('longitude')}")
                
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
    
    # Create and start the bridge
    bridge = MQTTtoInfluxBridge(BROKER_IP, BROKER_PORT, USER, PASSWORD, INFLUXDB_URL, INFLUXDB_TOKEN, INFLUXDB_ORG, INFLUXDB_BUCKET)
    
    try:
        bridge.start()
    except KeyboardInterrupt:
        bridge.stop()