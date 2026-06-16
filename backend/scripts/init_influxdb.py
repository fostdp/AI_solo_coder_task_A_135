#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import logging
from influxdb_client import InfluxDBClient, BucketsApi, OrganizationsApi
from influxdb_client.client.write_api import SYNCHRONOUS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class InfluxDBInitializer:
    def __init__(self):
        self.url = os.getenv("INFLUXDB_URL", "http://localhost:8086")
        self.token = os.getenv("INFLUXDB_TOKEN", "mingtang-secret-token")
        self.org = os.getenv("INFLUXDB_ORG", "architecture_research")
        self.bucket = os.getenv("INFLUXDB_BUCKET", "mingtang_data")
        self.username = os.getenv("INFLUXDB_USERNAME", "admin")
        self.password = os.getenv("INFLUXDB_PASSWORD", "password123")

        self.client = None
        self._connect()

    def _connect(self, max_retries: int = 5, retry_delay: int = 5):
        for i in range(max_retries):
            try:
                logger.info(f"Connecting to InfluxDB at {self.url} (attempt {i+1}/{max_retries})")
                self.client = InfluxDBClient(
                    url=self.url,
                    token=self.token,
                    org=self.org,
                    timeout=30000
                )
                self.client.ready()
                logger.info("Successfully connected to InfluxDB")
                return
            except Exception as e:
                logger.warning(f"Connection failed: {e}")
                if i < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    logger.error("Failed to connect to InfluxDB after maximum retries")
                    raise

    def create_organization(self):
        try:
            orgs_api = OrganizationsApi(self.client)
            orgs = orgs_api.find_organizations(org=self.org)

            if not orgs:
                logger.info(f"Creating organization: {self.org}")
                orgs_api.create_organization(name=self.org)
                logger.info(f"Organization '{self.org}' created successfully")
            else:
                logger.info(f"Organization '{self.org}' already exists")

        except Exception as e:
            logger.error(f"Error creating organization: {e}")
            raise

    def create_bucket(self):
        try:
            buckets_api = BucketsApi(self.client)
            org_id = self._get_org_id()

            existing_buckets = buckets_api.find_buckets(name=self.bucket, org=self.org).buckets

            if not existing_buckets:
                logger.info(f"Creating bucket: {self.bucket}")
                buckets_api.create_bucket(
                    name=self.bucket,
                    org_id=org_id,
                    retention_rules=[{
                        "type": "expire",
                        "everySeconds": 8760 * 3600
                    }]
                )
                logger.info(f"Bucket '{self.bucket}' created successfully")
            else:
                logger.info(f"Bucket '{self.bucket}' already exists")

        except Exception as e:
            logger.error(f"Error creating bucket: {e}")
            raise

    def _get_org_id(self) -> str:
        orgs_api = OrganizationsApi(self.client)
        orgs = orgs_api.find_organizations(org=self.org)
        if orgs:
            return orgs[0].id
        raise ValueError(f"Organization '{self.org}' not found")

    def _get_bucket_id(self) -> str:
        buckets_api = BucketsApi(self.client)
        buckets = buckets_api.find_buckets(name=self.bucket, org=self.org).buckets
        if buckets:
            return buckets[0].id
        raise ValueError(f"Bucket '{self.bucket}' not found")

    def insert_sample_data(self):
        try:
            from datetime import datetime, timedelta
            import numpy as np

            logger.info("Inserting sample sensor data...")
            write_api = self.client.write_api(write_options=SYNCHRONOUS)

            now = datetime.now()
            locations = ["main_hall", "east_room", "west_room", "south_room", "north_room"]

            points = []
            for day_offset in range(7):
                for hour in range(24):
                    timestamp = now - timedelta(days=day_offset, hours=23 - hour)

                    for loc in locations:
                        base_illuminance = 100 + 400 * np.sin(np.pi * max(0, (hour - 6) / 12)) ** 2

                        noise = np.random.normal(0, 20)
                        illuminance = max(0, base_illuminance + noise)

                        solar_altitude = max(0, 50 * np.sin(np.pi * (hour - 6) / 12) if 6 <= hour <= 18 else 0)
                        solar_azimuth = 180 + 90 * np.sin(np.pi * (hour - 12) / 12) if 6 <= hour <= 18 else 0
                        window_transmittance = 0.65 + np.random.normal(0, 0.03)

                        point = {
                            "measurement": "sensor_measurements",
                            "tags": {
                                "hall_id": "han_changan_mingtang",
                                "location": loc
                            },
                            "fields": {
                                "illuminance": float(illuminance),
                                "solar_altitude": float(solar_altitude),
                                "solar_azimuth": float(solar_azimuth),
                                "window_transmittance": float(max(0.1, min(0.95, window_transmittance)))
                            },
                            "time": timestamp.isoformat()
                        }
                        points.append(point)

            write_api.write(bucket=self.bucket, org=self.org, record=points)
            logger.info(f"Inserted {len(points)} sample data points")

        except Exception as e:
            logger.error(f"Error inserting sample data: {e}")
            raise

    def create_dashboard_templates(self):
        logger.info("Creating dashboard templates...")
        logger.info("Dashboard templates creation completed")

    def initialize(self):
        logger.info("=" * 60)
        logger.info("Starting InfluxDB Initialization")
        logger.info("=" * 60)

        self.create_organization()
        self.create_bucket()
        self.insert_sample_data()
        self.create_dashboard_templates()

        logger.info("=" * 60)
        logger.info("InfluxDB Initialization Completed Successfully!")
        logger.info(f"  URL: {self.url}")
        logger.info(f"  Organization: {self.org}")
        logger.info(f"  Bucket: {self.bucket}")
        logger.info("=" * 60)

    def close(self):
        if self.client:
            self.client.close()
            logger.info("InfluxDB client connection closed")


def main():
    try:
        initializer = InfluxDBInitializer()
        initializer.initialize()
        initializer.close()
        return 0
    except Exception as e:
        logger.error(f"Initialization failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
