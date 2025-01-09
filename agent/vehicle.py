import csv
import json
import paho.mqtt.client as mqtt
from time import sleep

# CSV file parameters
SOURCE_FILE = "C:\\Users\\louim\\Downloads\\SubData_10_03_2022.csv"
LINE_SKIP_AT_START_OF_FILE = 1
COLUMNS = ['id', 'stationid', 'referenceposition_latitude', 'heading_headingvalue', 'referenceposition_longitude', 'speed_speedvalue', 'referenceposition_altitude_altitudevalue', 'generationtime']
NEEDED_COLUMNS = ['generationtime', 'speed_speedvalue', 'referenceposition_latitude', 'referenceposition_longitude']

# Data parameter
DATA_VOLUME = 100000
REJECT_IF_SPEED_ZERO = True

#MQTT parameters
BROKER_IP = "localhost"
BROKER_PORT = 1883
KEEP_ALIVE = 60
TOPIC = "traffic/info"
USER = "user"
PASSWORD = "password"

# DEBUG -- print data instead of sending data via MQTT
DEBUG = False

def on_connect(client, _userdata, _flags, reason_code, _properties):
    print(f"Connected with result code {reason_code}")
    client.subscribe(TOPIC)

#def on_message(_client, _userdata, message):
#    print(f"Received message from {message.topic}: {str(message.payload)}")

def get_data_from_row(row, columns):
    if len(columns) == 0:
        return row
    row_data = []
    for column in columns:
        row_data.append(row[COLUMNS.index(column)])
    return row_data

def compute_row(row, columns):
    row_data = get_data_from_row(row, columns)
    return row_data
    
def get_data(source_file, line_skip = 0, columns = [], number_of_lines = -1):
    data = []
    with open(source_file, mode='r', newline='') as file:
        reader = csv.reader(file)
        line = 0
        for row in reader:
            if line == number_of_lines + line_skip:
                break
            line += 1
            if line <= line_skip:
                continue
            computed_row = compute_row(row, columns)
            if(REJECT_IF_SPEED_ZERO and computed_row[NEEDED_COLUMNS.index("speed_speedvalue")] == "0.0"):
                continue
            data.append(computed_row)
    return data  

def get_JSON_row(row):
    named_row = {
        "timestamp" : row[0],
        "speed" : float(row[1]),
        "latitude" : float(row[2]),
        "longitude" : float(row[3])
    }
    return json.dumps(named_row)

def send_row(row, mqtt_client):
    request = mqtt_client.publish(TOPIC, get_JSON_row(row), qos=1)
    request.wait_for_publish()

def get_MQTT_client():
    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    mqtt_client.on_connect = on_connect
    #mqtt_client.on_message = on_message

    mqtt_client.username_pw_set(USER, PASSWORD)
    mqtt_client.connect(BROKER_IP, BROKER_PORT, KEEP_ALIVE)

    mqtt_client.loop_start()
    return mqtt_client

def send_data(data):
    if DEBUG:
       for row in data:
            print(get_JSON_row(row))
    else :
        mqtt_client = get_MQTT_client()
        for row in data:
            send_row(row, mqtt_client)
        sleep(1)
        mqtt_client.disconnect()

def main():
    data = get_data(SOURCE_FILE, LINE_SKIP_AT_START_OF_FILE, NEEDED_COLUMNS, DATA_VOLUME)
    sorted_data = sorted(data)
    send_data(sorted_data)

if __name__ == "__main__":
    main()
