#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import logging
import random
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

import httpx
from pysolar.solar import get_altitude, get_azimuth
import numpy as np

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MingtangSensorSimulator:
    def __init__(
        self,
        api_url: str = "http://localhost:8000",
        hall_id: str = "han_changan_mingtang",
        latitude: float = 34.2658,
        longitude: float = 108.9541,
        interval: int = 3600
    ):
        self.api_url = api_url.rstrip('/')
        self.hall_id = hall_id
        self.latitude = latitude
        self.longitude = longitude
        self.interval = interval

        self.sensor_locations = [
            ("main_hall", 0.0, 0.0, 1.5),
            ("east_room", 8.0, 0.0, 1.5),
            ("west_room", -8.0, 0.0, 1.5),
            ("south_room", 0.0, 8.0, 1.5),
            ("north_room", 0.0, -8.0, 1.5),
            ("center_altar", 0.0, 0.0, 2.0)
        ]

        self.window_transmittance_base = 0.65
        self.weather_factor = 1.0

        logger.info(f"Initialized sensor simulator for {hall_id}")
        logger.info(f"Location: {latitude}°N, {longitude}°E")
        logger.info(f"Reporting interval: {interval}s")

    def calculate_solar_position(self, dt: datetime) -> Tuple[float, float]:
        try:
            altitude = get_altitude(self.latitude, self.longitude, dt)
            azimuth = get_azimuth(self.latitude, self.longitude, dt)
            return max(0.0, altitude), azimuth
        except Exception as e:
            logger.warning(f"Error calculating solar position: {e}")
            return 0.0, 0.0

    def calculate_illuminance(
        self,
        altitude: float,
        azimuth: float,
        location: Tuple[str, float, float, float],
        transmittance: float
    ) -> float:
        if altitude <= 0:
            return random.uniform(5, 15)

        direct_normal_irradiance = 1000 * np.sin(np.radians(altitude))
        diffuse_irradiance = 150 + 100 * np.sin(np.radians(altitude))

        loc_name, x, y, z = location

        azimuth_rad = np.radians(azimuth)
        sun_direction = np.array([
            np.sin(azimuth_rad) * np.cos(np.radians(altitude)),
            np.cos(azimuth_rad) * np.cos(np.radians(altitude)),
            np.sin(np.radians(altitude))
        ])

        sensor_pos = np.array([x, y, z])
        distance_from_center = np.sqrt(x**2 + y**2)
        center_attenuation = max(0.3, 1.0 - distance_from_center / 20.0)

        window_factors = {
            "main_hall": 1.0,
            "east_room": 0.9 if 90 < azimuth < 180 else 0.5,
            "west_room": 0.9 if 180 < azimuth < 270 else 0.5,
            "south_room": 0.9 if 135 < azimuth < 225 else 0.5,
            "north_room": 0.6,
            "center_altar": 1.1
        }

        window_factor = window_factors.get(loc_name, 0.8)

        orientation_factor = max(0.1, np.dot(sun_direction[:2], np.array([x, y]) / max(1e-6, distance_from_center)) if distance_from_center > 0 else 1.0)

        direct_component = direct_normal_irradiance * transmittance * window_factor * center_attenuation
        diffuse_component = diffuse_irradiance * transmittance * 0.5

        total_illuminance = (direct_component + diffuse_component) * self.weather_factor

        noise = random.gauss(0, total_illuminance * 0.05)

        return max(0.0, total_illuminance + noise)

    def generate_sensor_data(self, dt: datetime) -> List[Dict]:
        altitude, azimuth = self.calculate_solar_position(dt)

        weather_variation = random.uniform(0.8, 1.05)
        self.weather_factor = self.weather_factor * 0.95 + weather_variation * 0.05

        data_points = []

        for location in self.sensor_locations:
            loc_name, x, y, z = location

            transmittance = self.window_transmittance_base + random.uniform(-0.02, 0.02)
            transmittance = max(0.5, min(0.85, transmittance))

            illuminance = self.calculate_illuminance(
                altitude, azimuth, location, transmittance
            )

            data_point = {
                "timestamp": dt.isoformat(),
                "hall_id": self.hall_id,
                "location": loc_name,
                "illuminance": round(illuminance, 2),
                "solar_altitude": round(altitude, 4),
                "solar_azimuth": round(azimuth, 4),
                "window_transmittance": round(transmittance, 4)
            }
            data_points.append(data_point)

        return data_points

    async def send_data(self, data: List[Dict]) -> bool:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.api_url}/api/sensor/data",
                    json={"data": data}
                )

                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"Successfully sent {len(data)} data points")
                    return True
                else:
                    logger.error(f"Failed to send data: HTTP {response.status_code} - {response.text}")
                    return False

        except Exception as e:
            logger.error(f"Error sending data: {e}")
            return False

    def send_data_sync(self, data: List[Dict]) -> bool:
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    f"{self.api_url}/api/sensor/data",
                    json={"data": data}
                )

                if response.status_code == 200:
                    logger.info(f"Successfully sent {len(data)} data points")
                    return True
                else:
                    logger.error(f"Failed to send data: HTTP {response.status_code} - {response.text}")
                    return False

        except Exception as e:
            logger.error(f"Error sending data: {e}")
            return False

    def generate_backfill_data(self, start_date: datetime, end_date: datetime) -> int:
        logger.info(f"Generating backfill data from {start_date} to {end_date}")

        total_points = 0
        current_date = start_date

        while current_date <= end_date:
            data = self.generate_sensor_data(current_date)
            if self.send_data_sync(data):
                total_points += len(data)

            current_date += timedelta(hours=1)

            if current_date.hour == 0:
                logger.info(f"Progress: {current_date.date()}, {total_points} points sent")

        logger.info(f"Backfill completed: {total_points} total points sent")
        return total_points

    def run_continuous(self):
        logger.info("Starting continuous sensor simulation...")
        logger.info("Press Ctrl+C to stop")

        try:
            while True:
                now = datetime.now()
                data = self.generate_sensor_data(now)

                for point in data:
                    loc = point['location']
                    lux = point['illuminance']
                    alt = point['solar_altitude']
                    logger.debug(f"{loc}: {lux:.1f} lux, sun alt: {alt:.1f}°")

                self.send_data_sync(data)

                time.sleep(self.interval)

        except KeyboardInterrupt:
            logger.info("Sensor simulation stopped by user")
        except Exception as e:
            logger.error(f"Simulation error: {e}")
            raise


def main():
    parser = argparse.ArgumentParser(description='Mingtang Sensor Simulator')
    parser.add_argument('--mode', choices=['continuous', 'backfill'], default='continuous',
                        help='Operation mode')
    parser.add_argument('--api-url', default='http://localhost:8000',
                        help='Backend API URL')
    parser.add_argument('--hall-id', default='han_changan_mingtang',
                        help='Hall identifier')
    parser.add_argument('--latitude', type=float, default=34.2658,
                        help='Latitude in degrees')
    parser.add_argument('--longitude', type=float, default=108.9541,
                        help='Longitude in degrees')
    parser.add_argument('--interval', type=int, default=3600,
                        help='Reporting interval in seconds')
    parser.add_argument('--backfill-days', type=int, default=7,
                        help='Number of days to backfill')

    args = parser.parse_args()

    simulator = MingtangSensorSimulator(
        api_url=args.api_url,
        hall_id=args.hall_id,
        latitude=args.latitude,
        longitude=args.longitude,
        interval=args.interval
    )

    if args.mode == 'backfill':
        end_date = datetime.now()
        start_date = end_date - timedelta(days=args.backfill_days)
        simulator.generate_backfill_data(start_date, end_date)
    else:
        simulator.run_continuous()


if __name__ == "__main__":
    main()
