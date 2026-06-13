import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const COLORS = {
  positive: '#22c55e',
  neutral: '#facc15',
  negative: '#ef4444',
};

export default function SentimentPieChart({ breakdown }) {
  const data = Object.entries(breakdown).map(([label, val]) => ({
    name: label.charAt(0).toUpperCase() + label.slice(1),
    value: val.count,
    label,
  }));

  return (
    <div className="chart-box">
      <h3>Sentiment Distribution</h3>
      <ResponsiveContainer width="100%" height={280}>
        <PieChart>
          <Pie
            data={data}
            dataKey="value"
            nameKey="name"
            cx="50%"
            cy="50%"
            outerRadius={90}
            label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
          >
            {data.map((entry) => (
              <Cell key={entry.label} fill={COLORS[entry.label]} />
            ))}
          </Pie>
          <Tooltip />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}