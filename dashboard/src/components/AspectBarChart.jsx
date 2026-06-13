import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

export default function AspectBarChart({ reviews }) {
  // Aggregate aspect counts by category and label
  const aggregated = {};

  reviews.forEach((review) => {
    (review.aspects || []).forEach((aspect) => {
      if (!aggregated[aspect.category]) {
        aggregated[aspect.category] = { category: aspect.category, positive: 0, neutral: 0, negative: 0 };
      }
      aggregated[aspect.category][aspect.label] += 1;
    });
  });

  const data = Object.values(aggregated);

  if (data.length === 0) {
    return (
      <div className="chart-box">
        <h3>Aspect Breakdown</h3>
        <p className="status">No aspect data available yet.</p>
      </div>
    );
  }

  return (
    <div className="chart-box">
      <h3>Aspect Breakdown</h3>
      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="category" />
          <YAxis allowDecimals={false} />
          <Tooltip />
          <Legend />
          <Bar dataKey="positive" stackId="a" fill="#22c55e" />
          <Bar dataKey="neutral" stackId="a" fill="#facc15" />
          <Bar dataKey="negative" stackId="a" fill="#ef4444" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}