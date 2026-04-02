'use client';

interface RootCauseCardProps {
  rootCause: string | null;
  confidence?: number;
  reasoning?: string;
  actions?: string[];
}

export default function RootCauseCard({ rootCause, confidence, reasoning, actions }: RootCauseCardProps) {
  if (!rootCause) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <p className="text-gray-500 text-sm">Diagnosis pending...</p>
      </div>
    );
  }

  const confidenceColor = (confidence || 0) >= 80 ? 'bg-green-500' :
    (confidence || 0) >= 50 ? 'bg-yellow-500' : 'bg-red-500';

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-5">
      <h3 className="text-lg font-semibold mb-3">Root Cause Analysis</h3>

      {/* Root cause */}
      <div className="bg-red-50 border-l-4 border-red-500 p-3 mb-4">
        <p className="font-medium text-red-800">{rootCause}</p>
      </div>

      {/* Confidence bar */}
      {confidence !== undefined && (
        <div className="mb-4">
          <div className="flex justify-between text-sm mb-1">
            <span className="text-gray-600">Confidence</span>
            <span className="font-medium">{confidence}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className={`h-2 rounded-full ${confidenceColor}`}
              style={{ width: `${confidence}%` }}
            />
          </div>
        </div>
      )}

      {/* AI Reasoning */}
      {reasoning && (
        <div className="mb-4">
          <h4 className="text-sm font-medium text-gray-700 mb-1">AI Reasoning</h4>
          <p className="text-sm text-gray-600">{reasoning}</p>
        </div>
      )}

      {/* Recommended Actions */}
      {actions && actions.length > 0 && (
        <div>
          <h4 className="text-sm font-medium text-gray-700 mb-2">Recommended Actions</h4>
          <ul className="space-y-1">
            {actions.map((action, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-gray-600">
                <span className="text-blue-500 mt-0.5">&#8226;</span>
                {action}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
