import axios from 'axios';
import type { SensorData, SimulationParams, SimulationStatus, AlertRecord, WindowSolution } from '@/types';

const api = axios.create({
  baseURL: '/api',
  timeout: 60000,
});

export const sensorAPI = {
  getLatest: (hall_id: string = 'han_changan_mingtang') =>
    api.get<SensorData[]>(`/sensor/latest`, { params: { hall_id } }),

  getData: (params: { hall_id?: string; start_time?: string; end_time?: string; location?: string; limit?: number }) =>
    api.get<SensorData[]>('/sensor/data', { params }),

  getStatistics: (params: { hall_id?: string; start_time?: string; end_time?: string }) =>
    api.get('/sensor/statistics', { params }),

  getSunshineHours: (params: { hall_id?: string; date?: string; threshold?: number }) =>
    api.get('/sensor/sunshine-hours', { params }),
};

export const simulationAPI = {
  run: (params: SimulationParams) =>
    api.post<SimulationStatus>('/simulation/run', params),

  getStatus: (task_id: string) =>
    api.get<SimulationStatus>(`/simulation/status/${task_id}`),

  getTasks: () =>
    api.get<SimulationStatus[]>('/simulation/tasks'),

  getResult: (task_id: string) =>
    api.get<SimulationStatus>(`/simulation/result/${task_id}`),

  cancel: (task_id: string) =>
    api.post(`/simulation/cancel/${task_id}`),
};

export const optimizationAPI = {
  run: (params: {
    hall_id?: string;
    num_windows?: number;
    population_size?: number;
    max_iterations?: number;
    date?: string;
    start_hour?: number;
    end_hour?: number;
    target_uniformity?: number;
  }) =>
    api.post<{ task_id: string; status: string }>('/optimization/run', params),

  getStatus: (task_id: string) =>
    api.get<{
      task_id: string;
      status: string;
      progress: number;
      message: string;
      result?: {
        best_solution: WindowSolution[];
        best_fitness: number;
        uniformity: number;
        convergence_curve: number[];
        iterations: number;
        avg_illuminance: number;
      };
    }>(`/optimization/status/${task_id}`),

  getTasks: () =>
    api.get('/optimization/tasks'),

  getResult: (task_id: string) =>
    api.get(`/optimization/result/${task_id}`),

  compare: (original_windows?: WindowSolution[], optimized_windows?: WindowSolution[]) =>
    api.post('/optimization/compare', { original_windows, optimized_windows }),
};

export const alertAPI = {
  check: (hall_id: string = 'han_changan_mingtang') =>
    api.post('/alert/check', null, { params: { hall_id } }),

  getHistory: (params?: { hall_id?: string; start_time?: string; end_time?: string; limit?: number }) =>
    api.get<AlertRecord[]>('/alert/history', { params }),

  sendTest: (hall_id: string = 'han_changan_mingtang') =>
    api.post('/alert/test', null, { params: { hall_id } }),
};

export default api;
