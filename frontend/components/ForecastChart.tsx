'use client';

interface ForecastPoint {
  ds: string;
  yhat: number;
  yhat_lower: number;
  yhat_upper: number;
}

interface ForecastChartProps {
  service: string;
  metric: string;
  forecast: ForecastPoint[];
  threshold?: number;
  breachPredicted?: boolean;
  hoursUntilBreach?: number | null;
  method?: string;
}

export default function ForecastChart({
  service,
  metric,
  forecast,
  threshold,
  breachPredicted,
  hoursUntilBreach,
  method,
}: ForecastChartProps) {
  if (!forecast || forecast.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-4">
        <h4 className="font-medium text-sm text-gray-500">{service} — {metric}</h4>
        <p className="text-xs text-gray-400 mt-2">No forecast data available</p>
      </div>
    );
  }

  // Calculate chart dimensions
  const values = forecast.map(p => p.yhat);
  const upperValues = forecast.map(p => p.yhat_upper);
  const lowerValues = forecast.map(p => p.yhat_lower);
  const allValues = [...values, ...upperValues, ...lowerValues];
  if (threshold) allValues.push(threshold);

  const minVal = Math.min(...allValues) * 0.9;
  const maxVal = Math.max(...allValues) * 1.1;
  const range = maxVal - minVal || 1;

  const width = 100;
  const height = 50;

  // Generate SVG path for the forecast line
  const toX = (i: number) => (i / (forecast.length - 1)) * width;
  const toY = (v: number) => height - ((v - minVal) / range) * height;

  const forecastPath = forecast
    .map((p, i) => `${i === 0 ? 'M' : 'L'}${toX(i).toFixed(1)},${toY(p.yhat).toFixed(1)}`)
    .join(' ');

  // Confidence band
  const upperPath = forecast.map((p, i) => `${toX(i).toFixed(1)},${toY(p.yhat_upper).toFixed(1)}`).join(' ');
  const lowerPath = forecast.map((p, i) => `${toX(i).toFixed(1)},${toY(p.yhat_lower).toFixed(1)}`).reverse().join(' ');
  const bandPath = `M${upperPath} L${lowerPath} Z`;

  // Threshold line Y
  const thresholdY = threshold ? toY(threshold) : null;

  // Find breach point
  const breachIndex = breachPredicted
    ? forecast.findIndex(p => p.yhat > (threshold || Infinity))
    : -1;

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <div className="flex items-center justify-between mb-2">
        <div>
          <h4 className="font-medium text-sm">{service} — {metric}</h4>
          <span className="text-xs text-gray-400">{method || 'forecast'}</span>
        </div>
        {breachPredicted && hoursUntilBreach != null && (
          <span className={`text-xs font-medium px-2 py-0.5 rounded ${
            hoursUntilBreach < 24 ? 'bg-red-100 text-red-700' :
            hoursUntilBreach < 72 ? 'bg-orange-100 text-orange-700' :
            'bg-yellow-100 text-yellow-700'
          }`}>
            Breach in {hoursUntilBreach < 24 ? `${hoursUntilBreach.toFixed(0)}h` : `${(hoursUntilBreach / 24).toFixed(1)}d`}
          </span>
        )}
      </div>

      <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-32" preserveAspectRatio="none">
        {/* Confidence band */}
        <path d={bandPath} fill="rgba(99, 102, 241, 0.1)" stroke="none" />

        {/* Threshold line */}
        {thresholdY !== null && (
          <line
            x1="0" y1={thresholdY.toFixed(1)}
            x2={width.toString()} y2={thresholdY.toFixed(1)}
            stroke="#ef4444" strokeWidth="0.3" strokeDasharray="2,2"
          />
        )}

        {/* Forecast line */}
        <path d={forecastPath} fill="none" stroke="#6366f1" strokeWidth="0.5" />

        {/* Breach point marker */}
        {breachIndex >= 0 && (
          <circle
            cx={toX(breachIndex).toFixed(1)}
            cy={toY(forecast[breachIndex].yhat).toFixed(1)}
            r="1"
            fill="#ef4444"
          />
        )}
      </svg>

      <div className="flex justify-between text-xs text-gray-400 mt-1">
        <span>{new Date(forecast[0].ds).toLocaleDateString()}</span>
        <span>
          {values[values.length - 1].toFixed(1)}
          {threshold ? ` / ${threshold}` : ''}
        </span>
        <span>{new Date(forecast[forecast.length - 1].ds).toLocaleDateString()}</span>
      </div>
    </div>
  );
}
