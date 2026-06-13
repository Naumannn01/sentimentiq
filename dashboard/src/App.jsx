import { useState, useEffect } from 'react';
import { api } from './api';
import SentimentPieChart from './components/SentimentPieChart';
import AspectBarChart from './components/AspectBarChart';
import ReviewTable from './components/ReviewTable';
import HotelSidebar from './components/HotelSidebar';
import './App.css';

function App() {
  const [hotels, setHotels] = useState([]);
  const [hotelName, setHotelName] = useState('');
  const [stats, setStats] = useState(null);
  const [reviews, setReviews] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Fetch hotel list on mount
  useEffect(() => {
    api.getHotels().then((res) => setHotels(res.data));
  }, []);

  const fetchData = async (name) => {
    if (!name.trim()) return;
    setLoading(true);
    setError('');
    setHotelName(name);
    try {
      const [statsRes, reviewsRes] = await Promise.all([
        api.getHotelStats(name),
        api.getReviews({ hotel_name: name }),
      ]);
      setStats(statsRes.data);
      setReviews(reviewsRes.data.results || []);
    } catch (err) {
      setError('No data found for this hotel.');
      setStats(null);
      setReviews([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="layout">
      <HotelSidebar
        hotels={hotels}
        selectedHotel={hotelName}
        onSelect={fetchData}
      />

      <div className="dashboard">
        <header>
          <h1>SentimentIQ Dashboard</h1>
          <p>Hotel Review Sentiment Analysis</p>
        </header>

        <div className="search-bar">
          <input
            type="text"
            placeholder="Or type a hotel name..."
            value={hotelName}
            onChange={(e) => setHotelName(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && fetchData(hotelName)}
          />
          <button onClick={() => fetchData(hotelName)}>Search</button>
        </div>

        {loading && <p className="status">Loading...</p>}
        {error && <p className="status error">{error}</p>}

        {!stats && !loading && (
          <p className="status">Select a hotel from the sidebar to view its sentiment breakdown.</p>
        )}

        {stats && (
          <>
            <div className="summary-cards">
              <div className="card">
                <h3>Total Reviews</h3>
                <p className="big-number">{stats.total_reviews}</p>
              </div>
              {Object.entries(stats.breakdown).map(([label, data]) => (
                <div className={`card sentiment-${label}`} key={label}>
                  <h3>{label.charAt(0).toUpperCase() + label.slice(1)}</h3>
                  <p className="big-number">{data.percentage}%</p>
                  <p className="sub-number">{data.count} reviews</p>
                </div>
              ))}
            </div>

            <div className="charts-row">
              <SentimentPieChart breakdown={stats.breakdown} />
              <AspectBarChart reviews={reviews} />
            </div>

            <ReviewTable reviews={reviews} />
          </>
        )}
      </div>
    </div>
  );
}

export default App;