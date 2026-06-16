import React, { useRef, useEffect, useMemo } from 'react';
import { useAppStore } from '@/store';
import { jetColorMap, formatIlluminance, generateLegendStops, illuminanceCategory } from '@/utils/colorMap';
import type { SimulationResult } from '@/types';

interface LightCloudMapProps {
  simulationResult: SimulationResult | null;
  width: number;
  height: number;
}

const LightCloudMap: React.FC<LightCloudMapProps> = ({
  simulationResult,
  width,
  height
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const { cloudMapOpacity, showCloudMap, selectedHour } = useAppStore();

  const drawCloudMap = () => {
    const canvas = canvasRef.current;
    if (!canvas || !simulationResult) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    canvas.width = width;
    canvas.height = height;
    ctx.clearRect(0, 0, width, height);

    if (!showCloudMap) return;

    const { grid_size, illuminance_matrix, max_illuminance, min_illuminance } = simulationResult;
    const nx = grid_size.x;
    const nz = grid_size.z;
    const ySlice = Math.floor(grid_size.y / 2);

    const padding = 60;
    const mapWidth = width - padding * 2;
    const mapHeight = height - padding * 2;

    const cellWidth = mapWidth / nx;
    const cellHeight = mapHeight / nz;

    ctx.save();
    ctx.globalAlpha = cloudMapOpacity;

    for (let i = 0; i < nx; i++) {
      for (let j = 0; j < nz; j++) {
        const illuminance = illuminance_matrix[i][ySlice][j];

        if (isNaN(illuminance) || illuminance < 0) continue;

        const [r, g, b, a] = jetColorMap(illuminance, min_illuminance, max_illuminance);

        ctx.fillStyle = `rgba(${r}, ${g}, ${b}, ${a / 255})`;
        ctx.fillRect(
          padding + i * cellWidth,
          padding + j * cellHeight,
          cellWidth + 0.5,
          cellHeight + 0.5
        );
      }
    }

    ctx.restore();

    ctx.strokeStyle = 'rgba(212, 175, 55, 0.6)';
    ctx.lineWidth = 2;
    ctx.strokeRect(padding, padding, mapWidth, mapHeight);

    ctx.fillStyle = '#D4AF37';
    ctx.font = 'bold 14px "Noto Serif SC", serif';
    ctx.textAlign = 'center';
    ctx.fillText('室内采光伪彩色云图（俯视切面 y=1.5m）', width / 2, 30);

    ctx.fillStyle = '#e8e8e8';
    ctx.font = '12px "Noto Serif SC", serif';
    ctx.textAlign = 'left';
    ctx.fillText('北', padding + mapWidth / 2, padding - 15);
    ctx.textAlign = 'right';
    ctx.fillText('南', padding + mapWidth / 2, padding + mapHeight + 30);
    ctx.textAlign = 'left';
    ctx.fillText('西', padding - 30, padding + mapHeight / 2 + 5);
    ctx.textAlign = 'right';
    ctx.fillText('东', padding + mapWidth + 30, padding + mapHeight / 2 + 5);

    const legendX = padding;
    const legendY = height - 40;
    const legendWidth = mapWidth;
    const legendHeight = 15;

    const gradient = ctx.createLinearGradient(legendX, 0, legendX + legendWidth, 0);
    const stops = generateLegendStops(min_illuminance, max_illuminance);
    stops.forEach((stop, idx) => {
      gradient.addColorStop(idx / (stops.length - 1), stop.color);
    });

    ctx.fillStyle = gradient;
    ctx.fillRect(legendX, legendY, legendWidth, legendHeight);

    ctx.strokeStyle = 'rgba(212, 175, 55, 0.8)';
    ctx.lineWidth = 1;
    ctx.strokeRect(legendX, legendY, legendWidth, legendHeight);

    ctx.fillStyle = '#e8e8e8';
    ctx.font = '10px "Noto Serif SC", serif';
    ctx.textAlign = 'center';
    stops.forEach((stop, idx) => {
      const x = legendX + (idx / (stops.length - 1)) * legendWidth;
      ctx.fillText(formatIlluminance(stop.value), x, legendY + legendHeight + 15);
      ctx.beginPath();
      ctx.moveTo(x, legendY);
      ctx.lineTo(x, legendY - 5);
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.5)';
      ctx.stroke();
    });

    const { avg_illuminance, uniformity } = simulationResult;
    const category = illuminanceCategory(avg_illuminance);

    ctx.fillStyle = '#e8e8e8';
    ctx.font = '11px "Noto Serif SC", serif';
    ctx.textAlign = 'left';
    ctx.fillText(`平均照度: ${formatIlluminance(avg_illuminance)} (${category.category})`, padding, height - 60);
    ctx.fillText(`采光均匀度: ${(uniformity * 100).toFixed(1)}%`, padding, height - 45);

    const currentHour = selectedHour;
    ctx.fillStyle = '#D4AF37';
    ctx.font = 'bold 12px "Noto Serif SC", serif';
    ctx.textAlign = 'right';
    ctx.fillText(`${currentHour.toString().padStart(2, '0')}:00`, width - padding, 30);
  };

  useEffect(() => {
    drawCloudMap();
  }, [simulationResult, width, height, cloudMapOpacity, showCloudMap, selectedHour]);

  const stats = useMemo(() => {
    if (!simulationResult) return null;
    return {
      max: simulationResult.max_illuminance,
      min: simulationResult.min_illuminance,
      avg: simulationResult.avg_illuminance,
      uniformity: simulationResult.uniformity,
      category: illuminanceCategory(simulationResult.avg_illuminance)
    };
  }, [simulationResult]);

  return (
    <div className="relative w-full h-full">
      <canvas
        ref={canvasRef}
        className="w-full h-full"
        style={{ display: showCloudMap ? 'block' : 'none' }}
      />

      {!simulationResult && (
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center p-6 glass-panel">
            <div className="text-4xl mb-3">☀️</div>
            <p className="text-gray-400 text-sm">运行采光仿真后显示伪彩色云图</p>
            <p className="text-gray-500 text-xs mt-2">请在右侧面板点击"运行仿真"</p>
          </div>
        </div>
      )}

      {stats && (
        <div className="absolute top-4 right-4 glass-panel p-3 text-xs space-y-1">
          <div className="font-semibold text-ancient-gold mb-2">当前时段数据</div>
          <div className="flex justify-between">
            <span className="text-gray-400">最大:</span>
            <span style={{ color: illuminanceCategory(stats.max).color }}>
              {formatIlluminance(stats.max)}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">最小:</span>
            <span style={{ color: illuminanceCategory(stats.min).color }}>
              {formatIlluminance(stats.min)}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">平均:</span>
            <span style={{ color: stats.category.color }}>
              {formatIlluminance(stats.avg)}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">均匀度:</span>
            <span className={stats.uniformity > 0.7 ? 'text-sensor-good' : stats.uniformity > 0.5 ? 'text-sensor-warning' : 'text-sensor-danger'}>
              {(stats.uniformity * 100).toFixed(1)}%
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

export default LightCloudMap;
