#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Callable, Tuple
from abc import ABC, abstractmethod
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class WindowParameters:
    position: np.ndarray
    size: np.ndarray
    transmittance: float = 0.7


@dataclass
class PSOParticle:
    position: np.ndarray
    velocity: np.ndarray
    best_position: np.ndarray
    best_fitness: float
    fitness: float = 0.0


@dataclass
class OptimizationResult:
    best_solution: List[WindowParameters]
    best_fitness: float
    uniformity: float
    convergence_curve: List[float]
    iterations: int
    avg_illuminance: float
    execution_time: float

    def to_dict(self) -> Dict:
        return {
            'best_solution': [
                {
                    'position': wp.position.tolist(),
                    'size': wp.size.tolist(),
                    'transmittance': float(wp.transmittance)
                }
                for wp in self.best_solution
            ],
            'best_fitness': float(self.best_fitness),
            'uniformity': float(self.uniformity),
            'convergence_curve': [float(x) for x in self.convergence_curve],
            'iterations': int(self.iterations),
            'avg_illuminance': float(self.avg_illuminance),
            'execution_time': float(self.execution_time)
        }


class ParticleSwarmOptimizer:
    def __init__(
        self,
        fitness_function: Callable[[List[WindowParameters]], Tuple[float, float, float]],
        num_windows: int = 4,
        population_size: int = 30,
        max_iterations: int = 100,
        w: float = 0.7,
        c1: float = 1.5,
        c2: float = 1.5,
        position_bounds: Optional[Tuple[np.ndarray, np.ndarray]] = None,
        size_bounds: Optional[Tuple[np.ndarray, np.ndarray]] = None,
        random_seed: Optional[int] = None
    ):
        self.fitness_function = fitness_function
        self.num_windows = num_windows
        self.population_size = population_size
        self.population_size = population_size
        self.max_iterations = max_iterations
        self.w = w
        self.c1 = c1
        self.c2 = c2
        self.position_bounds = position_bounds or (
            np.array([-10, -10, 0.5], dtype=np.float64),
            np.array([10, 10, 5], dtype=np.float64)
        )
        self.size_bounds = size_bounds or (
            np.array([1.0, 1.0], dtype=np.float64),
            np.array([3.0, 2.5], dtype=np.float64)
        )

        if random_seed is not None:
            np.random.seed(random_seed)

        self.particles: List[PSOParticle] = []
        self.global_best_position: Optional[np.ndarray] = None
        self.global_best_fitness: float = -np.inf
        self.convergence_curve: List[float] = []

    def _encode_solution_to_particle(self, windows: List[WindowParameters]) -> np.ndarray:
        encoded = []
        for wp in windows:
            encoded.extend(wp.position)
            encoded.extend(wp.size)
            encoded.append(wp.transmittance)
        return np.array(encoded, dtype=np.float64)

    def _particle_to_solution(self, particle_pos: np.ndarray) -> List[WindowParameters]:
        windows = []
        idx = 0
        for _ in range(self.num_windows):
            position = particle_pos[idx:idx+3].copy()
            idx += 3
            size = particle_pos[idx:idx+2].copy()
            idx += 2
            transmittance = particle_pos[idx]
            idx += 1
            windows.append(WindowParameters(
                position=position,
                size=size,
                transmittance=transmittance
            ))
        return windows

    def _initialize_particles(self):
        self.particles = []
        dims_per_window = 6

        for _ in range(self.population_size):
            position = np.zeros(self.num_windows * dims_per_window, dtype=np.float64)
            velocity = np.zeros_like(position)

            for i in range(self.num_windows):
                pos_idx = i * dims_per_window

                for j in range(3):
                    position[pos_idx + j] = np.random.uniform(
                        self.position_bounds[0][j],
                        self.position_bounds[1][j]
                    )
                    velocity[pos_idx + j] = np.random.uniform(-1, 1)

                for j in range(2):
                    position[pos_idx + 3 + j] = np.random.uniform(
                        self.size_bounds[0][j],
                        self.size_bounds[1][j]
                    )
                    velocity[pos_idx + 3 + j] = np.random.uniform(-0.5, 0.5)

                position[pos_idx + 5] = np.random.uniform(0.5, 0.85)
                velocity[pos_idx + 5] = np.random.uniform(-0.1, 0.1)

            windows = self._particle_to_solution(position)
            fitness, uniformity, avg_ill = self.fitness_function(windows)

            particle = PSOParticle(
                position=position,
                velocity=velocity,
                best_position=position.copy(),
                best_fitness=fitness,
                fitness=fitness
            )
            self.particles.append(particle)

            if fitness > self.global_best_fitness:
                self.global_best_fitness = fitness
                self.global_best_position = position.copy()

    def _clip_bounds(self, position: np.ndarray) -> np.ndarray:
        clipped = position.copy()
        dims_per_window = 6

        for i in range(self.num_windows):
            pos_idx = i * dims_per_window

            for j in range(3):
                clipped[pos_idx + j] = np.clip(
                    clipped[pos_idx + j],
                    self.position_bounds[0][j],
                    self.position_bounds[1][j]
                )

            for j in range(2):
                clipped[pos_idx + 3 + j] = np.clip(
                    clipped[pos_idx + 3 + j],
                    self.size_bounds[0][j],
                    self.size_bounds[1][j]
                )

            clipped[pos_idx + 5] = np.clip(clipped[pos_idx + 5], 0.5, 0.85)

        return clipped

    def _update_velocity(self, particle: PSOParticle) -> np.ndarray:
        r1 = np.random.random(particle.velocity.shape)
        r2 = np.random.random(particle.velocity.shape)

        cognitive = self.c1 * r1 * (particle.best_position - particle.position)
        social = self.c2 * r2 * (self.global_best_position - particle.position)

        new_velocity = self.w * particle.velocity + cognitive + social

        v_max = 2.0
        new_velocity = np.clip(new_velocity, -v_max, v_max)

        return new_velocity

    def optimize(self, callback: Optional[Callable[[int, float], None] = None) -> OptimizationResult:
        import time
        start_time = time.time()

        logger.info("Starting Particle Swarm Optimization...")
        logger.info(f"Population size: {self.population_size}, Max iterations: {self.max_iterations}")
        logger.info(f"Number of windows to optimize: {self.num_windows}")

        self._initialize_particles()
        self.convergence_curve = [self.global_best_fitness]

        best_uniformity = 0.0
        best_avg_ill = 0.0

        for iteration in range(self.max_iterations):
            for particle in self.particles:
                windows = self._particle_to_solution(particle.position)
                try:
                    fitness, uniformity, avg_ill = self.fitness_function(windows)
                except Exception as e:
                    logger.warning(f"Error evaluating fitness: {e}")
                    fitness = -np.inf

                particle.fitness = fitness

                if fitness > particle.best_fitness:
                    particle.best_fitness = fitness
                    particle.best_position = particle.position.copy()

                if fitness > self.global_best_fitness:
                    self.global_best_fitness = fitness
                    self.global_best_position = particle.position.copy()
                    best_uniformity = uniformity
                    best_avg_ill = avg_ill

            for particle in self.particles:
                particle.velocity = self._update_velocity(particle)
                particle.position += particle.velocity
                particle.position = self._clip_bounds(particle.position)

            self.convergence_curve.append(self.global_best_fitness)

            if callback is not None:
                callback(iteration + 1, self.global_best_fitness)

            if (iteration + 1) % 10 == 0:
                logger.info(f"Iteration {iteration + 1}/{self.max_iterations}, Best fitness: {self.global_best_fitness:.4f}")

            if len(self.convergence_curve) > 20:
                recent = self.convergence_curve[-20:]
                if max(recent) - min(recent) < 1e-6:
                    logger.info("Convergence reached, stopping early")
                    break

        best_windows = self._particle_to_solution(self.global_best_position)

        execution_time = time.time() - start_time

        logger.info(f"Optimization completed in {execution_time:.2f} seconds")
        logger.info(f"Best fitness: {self.global_best_fitness:.4f}")
        logger.info(f"Uniformity: {best_uniformity:.4f}")
        logger.info(f"Average illuminance: {best_avg_ill:.2f} lux")

        return OptimizationResult(
            best_solution=best_windows,
            best_fitness=self.global_best_fitness,
            uniformity=best_uniformity,
            convergence_curve=self.convergence_curve,
            iterations=len(self.convergence_curve) - 1,
            avg_illuminance=best_avg_ill,
            execution_time=execution_time
        )


class LightingFitnessEvaluator:
    def __init__(
        self,
        lighting_calculator,
        target_uniformity_weight: float = 0.6,
        avg_illuminance_weight: float = 0.4,
        min_avg_illuminance: float = 100.0,
        evaluation_times: Optional[List[datetime]] = None
    ):
        self.lighting_calculator = lighting_calculator
        self.w = target_uniformity_weight
        self.ill_weight = avg_illuminance_weight
        self.min_avg_ill = min_avg_illuminance

        if evaluation_times is None:
            now = datetime.now()
            self.evaluation_times = [
                datetime(now.year, now.month, now.day, 10),
                datetime(now.year, now.month, now.day, 12),
                datetime(now.year, now.month, now.day, 14),
            ]
        else:
            self.evaluation_times = evaluation_times

    def __call__(self, windows: List[WindowParameters]) -> Tuple[float, float, float]:
        window_configs = []
        for wp in windows:
            normal = self._get_normal_from_position(wp.position)
            window_configs.append({
                'position': wp.position.tolist(),
                'size': wp.size.tolist(),
                'normal': normal.tolist(),
                'up': [0, 0, 1],
                'transmittance': wp.transmittance
            })

        self.lighting_calculator.update_windows(window_configs)

        uniformities = []
        avg_illuminances = []

        for eval_time in self.evaluation_times:
            result = self.lighting_calculator.calculate_illuminance(eval_time)
            uniformities.append(result.uniformity)
            avg_illuminances.append(result.avg_illuminance)

        avg_uniformity = np.mean(uniformities)
        avg_ill = np.mean(avg_illuminances)

        uniformity_score = avg_uniformity

        if avg_ill >= self.min_avg_ill:
            illuminance_score = 1.0
        else:
            illuminance_score = avg_ill / self.min_avg_ill

        penalty = self._calculate_overlap_penalty(windows)

        fitness = (self.w * uniformity_score +
                   self.ill_weight * illuminance_score) * (1 - penalty)

        return fitness, avg_uniformity, avg_ill

    def _get_normal_from_position(self, position: np.ndarray) -> np.ndarray:
        x, y, z = position
        if abs(x) > abs(y):
            return np.array([1 if x > 0 else -1, 0, 0], dtype=np.float64)
        else:
            return np.array([0, 1 if y > 0 else -1, 0], dtype=np.float64)

    def _calculate_overlap_penalty(self, windows: List[WindowParameters]) -> float:
        penalty = 0.0
        for i in range(len(windows)):
            for j in range(i + 1, len(windows)):
                w1, w2 = windows[i], windows[j]
                dist = np.linalg.norm(w1.position[:2] - w2.position[:2])
                min_dist = np.mean(w1.size) + np.mean(w2.size)
                if dist < min_dist * 0.5:
                    penalty += 0.1 * (1 - dist / (min_dist * 0.5))
        return min(penalty, 0.5)
