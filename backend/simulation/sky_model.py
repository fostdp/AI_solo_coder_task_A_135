#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import numpy as np
from dataclasses import dataclass
from typing import Tuple, Optional
from abc import ABC, abstractmethod


@dataclass
class SkyModelParameters:
    solar_altitude: float
    solar_azimuth: float
    turbidity: float = 2.5
    ground_albedo: float = 0.2


class SkyModel(ABC):
    def __init__(self, params: SkyModelParameters):
        self.params = params
        self._validate_params()

    def _validate_params(self):
        if not (-90 <= self.params.solar_altitude <= 90):
            raise ValueError(f"Solar altitude must be between -90 and 90, got {self.params.solar_altitude}")
        if not (0 <= self.params.solar_azimuth <= 360):
            raise ValueError(f"Solar azimuth must be between 0 and 360, got {self.params.solar_azimuth}")

    @abstractmethod
    def get_sky_luminance(self, theta: float, phi: float) -> float:
        pass

    @abstractmethod
    def get_direct_irradiance(self) -> float:
        pass

    @abstractmethod
    def get_diffuse_irradiance(self) -> float:
        pass

    def get_sky_irradiance_on_surface(self, surface_normal: np.ndarray) -> float:
        sky_irradiance = self.get_diffuse_irradiance()

        cos_theta = np.clip(np.dot(surface_normal, np.array([0, 0, 1])), 0, 1)
        view_factor = (1 + cos_theta) / 2

        return sky_irradiance * view_factor


class CIEClearSky(SkyModel):
    def __init__(self, params: SkyModelParameters):
        super().__init__(params)
        self.zs = np.radians(90 - params.solar_altitude)

    def get_sky_luminance(self, theta: float, phi: float) -> float:
        theta_rad = np.radians(theta)
        phi_rad = np.radians(phi)
        zs_rad = self.zs

        cos_chi = (np.cos(zs_rad) * np.cos(theta_rad) +
                   np.sin(zs_rad) * np.sin(theta_rad) * np.cos(phi_rad - np.radians(self.params.solar_azimuth)))
        chi = np.arccos(np.clip(cos_chi, -1, 1))

        f1 = 0.91 + 10 * np.exp(-3 * chi) + 0.45 * cos_chi ** 2 - 0.01
        f2 = 1 + 0.91 * np.exp(-0.32 / np.cos(theta_rad)) if np.cos(theta_rad) > 0.01 else 1

        zenith_luminance = self._get_zenith_luminance()
        luminance = zenith_luminance * f1 * f2 / (0.274 + 0.908 * np.exp(-0.032 * zs_rad))

        return max(0, luminance)

    def _get_zenith_luminance(self) -> float:
        zs_deg = 90 - self.params.solar_altitude
        return (1000 * np.exp(-0.025 * zs_deg))

    def get_direct_irradiance(self) -> float:
        zs_deg = 90 - self.params.solar_altitude
        if zs_deg >= 90:
            return 0
        m = 1 / np.cos(np.radians(zs_deg)) if zs_deg < 85 else 35
        return 1367 * np.exp(-0.678 * self.params.turbidity * m) * np.cos(np.radians(zs_deg))

    def get_diffuse_irradiance(self) -> float:
        direct = self.get_direct_irradiance()
        return direct * 0.15


class CIEOvercastSky(SkyModel):
    def __init__(self, params: SkyModelParameters):
        super().__init__(params)

    def get_sky_luminance(self, theta: float, phi: float) -> float:
        theta_rad = np.radians(theta)
        zenith_luminance = self._get_zenith_luminance()
        return zenith_luminance * (1 + 2 * np.cos(theta_rad)) / 3

    def _get_zenith_luminance(self) -> float:
        solar_alt = max(0, self.params.solar_altitude)
        return 200 + 800 * np.sin(np.radians(solar_alt))

    def get_direct_irradiance(self) -> float:
        return 0

    def get_diffuse_irradiance(self) -> float:
        solar_alt = max(0, self.params.solar_altitude)
        return 150 + 300 * np.sin(np.radians(solar_alt))


class PerezSkyModel(SkyModel):
    COEFFICIENTS = {
        'luminance': np.array([
            [0.1787, -1.4630],
            [-0.3554, 0.4275],
            [-0.0227, 5.3251],
            [0.1206, -2.5771],
            [-0.0670, 0.3703]
        ])
    }

    def __init__(self, params: SkyModelParameters):
        super().__init__(params)
        self.zs = np.radians(90 - params.solar_altitude)
        self._precompute_coefficients()

    def _precompute_coefficients(self):
        a = self.COEFFICIENTS['luminance'][:, 0]
        b = self.COEFFICIENTS['luminance'][:, 1]
        self.abs_coeffs = a + b * self.params.turbidity

    def get_sky_luminance(self, theta: float, phi: float) -> float:
        if self.params.solar_altitude <= 0:
            return 0

        theta_rad = np.radians(theta)
        phi_rad = np.radians(phi)
        zs_rad = self.zs

        cos_chi = (np.cos(zs_rad) * np.cos(theta_rad) +
                   np.sin(zs_rad) * np.sin(theta_rad) * np.cos(phi_rad - np.radians(self.params.solar_azimuth)))
        chi = np.arccos(np.clip(cos_chi, -1, 1))

        abs_c = self.abs_coeffs

        phi_function = (1 + abs_c[0] * np.exp(abs_c[1] / np.cos(theta_rad))) * \
                       (1 + abs_c[2] * np.exp(abs_c[3] * chi) + abs_c[4] * cos_chi ** 2)

        if abs_c[0] + abs_c[2] + abs_c[4] == 0:
            normalization = 1.0
        else:
            normalization = (1 + abs_c[0] * np.exp(abs_c[1])) * \
                            (1 + abs_c[2] * np.exp(abs_c[3] * zs_rad) + abs_c[4] * np.cos(zs_rad) ** 2)

        zenith_luminance = self._get_zenith_luminance()
        luminance = zenith_luminance * phi_function / normalization

        return max(0, luminance)

    def _get_zenith_luminance(self) -> float:
        chi = np.radians(90 - self.params.solar_altitude)
        T = self.params.turbidity

        zenith_luminance = (
            (4.0453 * T - 4.9710) * np.tan((4/9 - T/120) * (np.pi - 2 * chi)) -
            0.2155 * T + 2.4192
        )

        return max(0, zenith_luminance * 1000)

    def get_direct_irradiance(self) -> float:
        if self.params.solar_altitude <= 0:
            return 0

        zs_deg = 90 - self.params.solar_altitude
        if zs_deg >= 90:
            return 0

        m = 1 / (np.cos(np.radians(zs_deg)) + 0.50572 * (96.07995 - zs_deg) ** (-1.6364))
        I0 = 1367.0
        k = 0.2709 * self.params.turbidity - 0.2909

        direct_normal = I0 * np.exp(-k * m)
        direct_horizontal = direct_normal * np.cos(np.radians(zs_deg))

        return max(0, direct_horizontal)

    def get_diffuse_irradiance(self) -> float:
        if self.params.solar_altitude <= 0:
            return 0

        direct = self.get_direct_irradiance()
        T = self.params.turbidity
        altitude_rad = np.radians(self.params.solar_altitude)

        diffuse_ratio = 0.095 + 0.04 * (T - 1)
        diffuse_ratio = diffuse_ratio * (1 - np.exp(-altitude_rad / 0.5))

        return max(0, direct * diffuse_ratio + 50 * np.sin(altitude_rad))


def create_sky_model(model_type: str, params: SkyModelParameters) -> SkyModel:
    models = {
        'perez': PerezSkyModel,
        'cie_clear': CIEClearSky,
        'cie_overcast': CIEOvercastSky
    }

    if model_type not in models:
        raise ValueError(f"Unknown sky model type: {model_type}. "
                         f"Available types: {list(models.keys())}")

    return models[model_type](params)
