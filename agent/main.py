from logging import info
from paho.mqtt import client as mqtt
import time
import json


def on_connect(client, _userdata, _flags, reason_code, _properties):
    print(f"Connected with result code {reason_code}")
    client.subscribe("iot")


def on_message(_client, _userdata, message):
    print(f"Received message from {message.topic}: {str(message.payload)}")


def main():
    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message

    mqtt_client.username_pw_set("user", "password")
    mqtt_client.connect("localhost", 1883, 60)

    # Blocking call that processes network traffic, dispatches callbacks and
    # handles reconnecting.
    # Other loop*() functions are available that give a threaded interface and a
    # manual interface.
    mqtt_client.loop_start()

    for x in range(0, 10):
        msg = {
            "message": f"Hello, World! {x}",
        }
        msg = json.dumps(msg)

        print(f"Publishing message: {msg}")
        infot = mqtt_client.publish("iot", msg, qos=1)
        infot.wait_for_publish()

        time.sleep(1)
    mqtt_client.disconnect()


if __name__ == "__main__":
    main()
