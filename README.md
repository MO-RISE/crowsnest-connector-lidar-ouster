# crowsnest-connector-lidar-ouster

A crowsnest microservice for connecting to an [Ouster Lidar SDK 0.8.1](https://static.ouster.dev/sdk-docs/index.html) 

## How it works

For now, this microservice just does the basics.

* Connects to an already configured Ouster sensor
* Listens on the continuous stream of LidarScanPackets
* Transform these to the NED frame (requires manual input for now and assumes a static sensor)
* Wraps into a brefv message and outputs over MQTT
* TODO: Output to file
* TODO: Flag for connecting to MQTT broker

For configuring the sensor hardware, the [TCP API](https://static.ouster.dev/sensor-docs/image_route1/image_route2/common_sections/API/tcp-api.html) is recommended.

### Typical setup (docker-compose)

```yaml
version: '3'
services:

  ouster-lidar:
    image: ghcr.io/mo-rise/crowsnest-connector-lidar-ouster:latest
    restart: unless-stopped
    network_mode: "host"
    environment:
      - MQTT_BROKER_HOST=localhost
      - MQTT_BROKER_PORT=1883
      - MQTT_TOPIC_POINTCLOUD=CROWSNEST/<platform>/LIDAR/<device_id>/POINTCLOUD
      - OUSTER_HOSTNAME=<IP of sensor>
      - OUSTER_ATTITUDE=90,45,180
      - POINTCLOUD_FREQUENCY=2
```

## Development setup

To setup the development environment:

    python3 -m venv venv
    source ven/bin/activate

Install everything thats needed for development:

    pip install -r requirements_dev.txt

To run the linters:

    black main.py tests
    pylint main.py

To run the tests:

    no automatic tests yet...


## License
Apache 2.0, see [LICENSE](./LICENSE)