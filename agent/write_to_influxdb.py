from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from datetime import datetime

# Your credentials
INFLUXDB_URL = "http://localhost:8086"
INFLUXDB_TOKEN = "lkvv1hrjdcCBqx5iNq9qY_TNJNNf8_e_C93iCp6pU7PgBdUnZqR235nybYu2a_CkKLEhTmSMy2TNkUvJhMGLKA=="
INFLUXDB_ORG = "LMO"
INFLUXDB_BUCKET = "IoT"

# Create a test write
client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
write_api = client.write_api(write_options=SYNCHRONOUS)

test_point = Point("info")\
    .field("speed", 60.5)\
    .field("lat", 45.5)\
    .field("long", -73.5)\
    .time(datetime.now())

write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=test_point)