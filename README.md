# crowsnest-connector-lidar-ouster

A crowsnest microservice for connecting to an [Ouster Lidar SDK 0.8.1](https://static.ouster.dev/sdk-docs/index.html) 

## How it works

For now, this microservice just does the basics.

* Connects to an already configured Ouster sensor
* Listens on the continuous stream of LidarScanPackets
* Transform these to the NED frame (requires manual input for now and assumes a static sensor)
* Wraps into a brefv message and outputs over MQTT
* TODO: Container output to file


For configuring the sensor hardware, the [TCP API](https://static.ouster.dev/sensor-docs/image_route1/image_route2/common_sections/API/tcp-api.html) is recommended.

### Typical setup (docker-compose)

See also `docker-compose.example.yml`

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

OUSTER-SDK only supporting not higher then python 3.9 (2023-06-02)  

To setup the development environment:

```bach
    python3 -m venv venv
    source ven/bin/activate
```

Install everything thats needed for development:

```bach
    pip install -r requirements_dev.txt
```

To run the linters:

```bach
    black main.py tests
    pylint main.py
```

To run the tests:
    no automatic tests yet...


In addition, code for brefv must be generated using the following commands:

```bach
mkdir brefv
datamodel-codegen --input brefv/envelope.json --input-file-type jsonschema --output brefv/envelope.py
datamodel-codegen --input brefv/messages --input-file-type jsonschema  --reuse-model --output brefv/messages
```

## License

Apache 2.0, see [LICENSE](./LICENSE)