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
      <div style={{
        padding: 20, borderRadius: 14,
        background: 'rgba(255,255,255,0.02)',
        border: '1px solid rgba(255,255,255,0.04)',
      }}>
        <h4 style={{ fontSize: 13, fontWeight: 600, color: '#71717a' }}>{service} -- {metric}</h4>
        <p style={{ fontSize: 12, color: '#3f3f46', marginTop: 8 }}>No forecast data available</p>
      </div>
    );
  }

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
  const toX = (i: number) => (i / (forecast.length - 1)) * width;
  const toY = (v: number) => height - ((v - minVal) / range) * height;

  const forecastPath = forecast
    .map((p, i) => `${i === 0 ? 'M' : 'L'}${toX(i).toFixed(1)},${toY(p.yhat).toFixed(1)}`)
    .join(' ');

  const upperPath = forecast.map((p, i) => `${toX(i).toFixed(1)},${toY(p.yhat_upper).toFixed(1)}`).join(' ');
  const lowerPath = forecast.map((p, i) => `${toX(i).toFixed(1)},${toY(p.yhat_lower).toFixed(1)}`).reverse().join(' ');
  const bandPath = `M${upperPath} L${lowerPath} Z`;
  const thresholdY = threshold ? toY(threshold) : null;
  const breachIndex = breachPredicted ? forecast.findIndex(p => p.yhat > (threshold || Infinity)) : -1;

  const urgencyColor = !breachPredicted ? '#71717a'
    : (hoursUntilBreach ?? 999) < 24 ? '#ef4444'
    : (hoursUntilBreach ?? 999) < 72 ? '#f59e0b' : '#f59e0b';

  return (
    <div style={{
      padding: 20, borderRadius: 14,
      background: 'rgba(255,255,255,0.02)',
      border: '1px solid rgba(255,255,255,0.04)',
      transition: 'all 0.2s',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 14 }}>
        <div>
          <h4 style={{ fontSize: 13, fontWeight: 600, color: '#e2e8f0', marginBottom: 2 }}>{service} -- {metric}</h4>
          <span style={{ fontSize: 10, color: '#52525b' }}>{method || 'forecast'}</span>
        </div>
        {breachPredicted && hoursUntilBreach != null && (
          <span style={{
            fontSize: 10, fontWeight: 700, color: urgencyColor,
            padding: '3px 10px', borderRadius: 6,
            background: `${urgencyColor}12`,
            border: `1px solid ${urgencyColor}25`,
          }}>
            Breach in {hoursUntilBreach < 24 ? `${hoursUntilBreach.toFixed(0)}h` : `${(hoursUntilBreach / 24).toFixed(1)}d`}
          </span>
        )}
      </div>

      <svg viewBox={`0 0 ${width} ${height}`} style={{ width: '100%', height: 120 }} preserveAspectRatio="none">
        {/* Confidence band */}
        <path d={bandPath} fill="rgba(139,92,246,0.08)" stroke="none" />
        {/* Threshold line */}
        {thresholdY !== null && (
          <line x1="0" y1={thresholdY.toFixed(1)} x2={width.toString()} y2={thresholdY.toFixed(1)}
            stroke="#ef4444" strokeWidth="0.3" strokeDasharray="2,2" />
        )}
        {/* Forecast line */}
        <path d={forecastPath} fill="none" stroke="#8b5cf6" strokeWidth="0.6"
          style={{ filter: 'drop-shadow(0 0 2px rgba(139,92,246,0.4))' }} />
        {/* Breach point */}
        {breachIndex >= 0 && (
          <circle cx={toX(breachIndex).toFixed(1)} cy={toY(forecast[breachIndex].yhat).toFixed(1)}
            r="1.2" fill="#ef4444" style={{ filter: 'drop-shadow(0 0 3px rgba(239,68,68,0.6))' }} />
        )}
      </svg>

      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 8 }}>
        <span style={{ fontSize: 10, color: '#3f3f46' }}>
          {new Date(forecast[0].ds).toLocaleDateString()}
        </span>
        <span style={{ fontSize: 10, color: '#71717a', fontFamily: 'monospace' }}>
          {values[values.length - 1].toFixed(1)}
          {threshold ? ` / ${threshold}` : ''}
        </span>
        <span style={{ fontSize: 10, color: '#3f3f46' }}>
          {new Date(forecast[forecast.length - 1].ds).toLocaleDateString()}
        </span>
      </div>
    </div>
  );
}
