import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

export default function SentimentTrendChart({ data }) {
  if (!data || data.length < 2) {
    return (
      <div className="chart-box">
        <h3>Sentiment Trend</h3>
        <p className="status">Not enough data across multiple days yet — keep submitting reviews to build this chart.</p>
      </div>
    );
  }

  return (
    <div className="chart-box">
      <h3>Sentiment Trend</h3>
      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" />
          <YAxis allowDecimals={false} />
          <Tooltip />
          <Legend />
          <Line type="monotone" dataKey="positive" stroke="#22c55e" strokeWidth={2} />
          <Line type="monotone" dataKey="neutral" stroke="#facc15" strokeWidth={2} />
          <Line type="monotone" dataKey="negative" stroke="#ef4444" strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}