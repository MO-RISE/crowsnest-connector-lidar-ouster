"""Main entrypoint for this application"""
import logging
import warnings
import threading
from contextlib import closing
from functools import partial
from datetime import datetime, timezone

import numpy as np
from scipy.spatial.transform import Rotation
from streamz import Stream
from environs import Env
from paho.mqtt.client import Client as MQTT
from ouster import client

from brefv.envelope import Envelope


# Reading config from environment variables
env = Env()

MQTT_BROKER_HOST: str = env("MQTT_BROKER_HOST")
MQTT_BROKER_PORT: int = env.int("MQTT_BROKER_PORT", 1883)
MQTT_CLIENT_ID: str = env("MQTT_CLIENT_ID", None)
MQTT_TRANSPORT: str = env("MQTT_TRANSPORT", "tcp")
MQTT_TLS: bool = env.bool("MQTT_TLS", False)
MQTT_USER: str = env("MQTT_USER", None)
MQTT_PASSWORD: str = env("MQTT_PASSWORD", None)

MQTT_TOPIC_POINTCLOUD: str = env("MQTT_TOPIC_POINTCLOUD")

OUSTER_HOSTNAME: str = env("OUSTER_HOSTNAME")

# These are a set of Euler angles (roll, pitch, yaw) taking us from the platform body
# frame to the Sensor frame, as defined in the Sensor documentation.
OUSTER_ATTITUDE: list = env.list(
    "OUSTER_ATTITUDE", [0, 0, 0], subcast=float, validate=lambda x: len(x) == 3
)
POINTCLOUD_FREQUENCY = env.float("POINTCLOUD_FREQUENCY", default=2)

LOG_LEVEL = env.log_level("LOG_LEVEL", logging.WARNING)


# Setup logger
logging.basicConfig(level=LOG_LEVEL)
logging.captureWarnings(True)
warnings.filterwarnings("once")
LOGGER = logging.getLogger("crowsnest-connector-lidar-ouster")

# Create mqtt client and configure it according to configuration
mq = MQTT(client_id=MQTT_CLIENT_ID, transport=MQTT_TRANSPORT)
mq.username_pw_set(MQTT_USER, MQTT_PASSWORD)
if MQTT_TLS:
    mq.tls_set()

mq.enable_logger(LOGGER)


def rotate_pcd(pcd: np.ndarray, attitude: list) -> np.ndarray:
    """Rotate pcd according to the sensor attitude

    Args:
        pcd (np.ndarray): The un-rotated point cloud (in sensor frame)
        attitude (np.ndarray): The attitude of the sensor ([roll, pitch, yaw]) in degrees

    Returns:
        np.ndarray: The rotated point cloud (in NED frame)
    """
    points = pcd.reshape(-1, pcd.shape[-1])
    LOGGER.debug("Rotating %d points using attitude: %s", len(points), attitude)
    transform = Rotation.from_euler("zyx", attitude[::-1], degrees=True)
    return transform.apply(points)


def to_brefv(pcd: np.ndarray) -> Envelope:
    """From point cloud to brefv envelope"""

    envelope = Envelope(
        sent_at=datetime.now(timezone.utc).isoformat(),
        message=pcd.tolist(),
    )

    LOGGER.debug("Assembled into brefv envelope: %s", envelope)

    return envelope


def to_mqtt(envelope: dict):
    """Publish an envelope to a mqtt topic"""

    topic = MQTT_TOPIC_POINTCLOUD
    payload = envelope.json()

    LOGGER.debug("Publishing on %s with payload: %s", topic, payload)
    try:
        mq.publish(
            topic,
            payload,
        )
    except Exception:  # pylint: disable=broad-except
        LOGGER.exception("Failed publishing to broker!")


if __name__ == "__main__":

    # Build pipeline
    LOGGER.info("Building pipeline...")
    source = Stream()
    source.latest().rate_limit(1 / POINTCLOUD_FREQUENCY).map(
        partial(rotate_pcd, attitude=OUSTER_ATTITUDE)
    ).map(to_brefv).sink(to_mqtt)

    LOGGER.info("Connecting to MQTT broker...")
    mq.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT)

    # Ouster SDK runs in the foreground so we put the MQTT stuff in a separate thread
    threading.Thread(target=mq.loop_forever, daemon=True).start()

    LOGGER.info("Connecting to Ouster sensor...")

    # Connect with the Ouster sensor and start processing lidar scans
    config = client.get_config(OUSTER_HOSTNAME)
    LOGGER.info("Sensor configuration: \n %s", config)

    LOGGER.info("Processing packages!")

    with closing(
        client.Scans.stream(OUSTER_HOSTNAME, config.udp_port_lidar, complete=True)
    ) as stream:

        # Create a look-up table to cartesian projection
        xyz_lut = client.XYZLut(stream.metadata)

        for scan in stream:

            # obtain destaggered xyz representation
            xyz_destaggered = client.destagger(stream.metadata, xyz_lut(scan))

            source.emit(xyz_destaggered)
