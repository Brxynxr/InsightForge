interface MetricsDisplayProps {
  metrics: Record<string, number>;
}

export default function MetricsDisplay({ metrics }: MetricsDisplayProps) {
  const formatNumber = (value: number) => {
    if (value >= 1000000) return `${(value / 1000000).toFixed(1)}M`;
    if (value >= 1000) return `${(value / 1000).toFixed(1)}K`;
    return value.toString();
  };

  const metricItems = Object.entries(metrics).map(([key, value]) => ({
    label: key.replace(/_/g, " ").toUpperCase(),
    value,
  }));

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {metricItems.map((item) => (
        <div key={item.label} className="bg-gray-50 rounded-lg p-4 text-center">
          <p className="text-2xl font-bold text-gray-900">
            {typeof item.value === "number" && !Number.isInteger(item.value)
              ? item.value.toFixed(2)
              : formatNumber(item.value)}
          </p>
          <p className="text-xs text-gray-600 mt-1">{item.label}</p>
        </div>
      ))}
    </div>
  );
}
