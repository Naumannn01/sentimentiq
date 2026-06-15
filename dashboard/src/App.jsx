import { useState, useEffect } from 'react';
import { api } from './api';
import WebhookManager from './components/WebhookManager';
import SentimentPieChart from './components/SentimentPieChart';
import AspectBarChart from './components/AspectBarChart';
import ReviewTable from './components/ReviewTable';
import HotelSidebar from './components/HotelSidebar';
import ReviewSubmitForm from './components/ReviewSubmitForm';
import EmptyState from './components/EmptyState';
import SentimentTrendChart from './components/SentimentTrendChart';
import toast, { Toaster } from 'react-hot-toast';
import './App.css';

function App() {
  const [hotels, setHotels] = useState([]);
  const [hotelName, setHotelName] = useState('');
  const [stats, setStats] = useState(null);
  const [reviews, setReviews] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('dashboard'); // 'dashboard' | 'webhooks';
  const [noReviews, setNoReviews] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [trend, setTrend] = useState([]);

  // Fetch hotel list on mount
  useEffect(() => {
    api.getHotels().then((res) => setHotels(res.data));
  }, []);

  const fetchData = async (name) => {
    if (!name.trim()) return;
    setLoading(true);
    setError('');
    setNoReviews(false);
    setHotelName(name);
    setSidebarOpen(false); // auto-close on mobile after selecting

    try {
      const [statsRes, reviewsRes, trendRes] = await Promise.all([
        api.getHotelStats(name),
        api.getReviews({ hotel_name: name }),
        api.getHotelTrend(name).catch(() => ({ data: [] })),
      ]);
      setStats(statsRes.data);
      setReviews(reviewsRes.data.results || []);
      setTrend(trendRes.data);

    } catch (err) {
      if (err.response?.status === 404) {
        setNoReviews(true);
        setStats(null);
        setReviews([]);
      } else {
        toast.error('Something went wrong loading this hotel.');
        setStats(null);
        setReviews([]);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-shell">
      <Toaster position="top-right" toastOptions={{ style: { background: '#1e293b', color: '#e2e8f0', border: '1px solid #334155' } }} />
      <nav className="top-nav">
        <div className="nav-left">
          <button className="sidebar-toggle" onClick={() => setSidebarOpen(!sidebarOpen)}>
            ☰
          </button>
          <span className="brand">SentimentIQ</span>
        </div>
        <div className="tabs">
          <button
            className={activeTab === 'dashboard' ? 'active' : ''}
            onClick={() => setActiveTab('dashboard')}
          >
            Dashboard
          </button>
          <button
            className={activeTab === 'webhooks' ? 'active' : ''}
            onClick={() => setActiveTab('webhooks')}
          >
            Webhooks
          </button>
        </div>
      </nav>

      {activeTab === 'dashboard' && (
        <div className="layout">
          <HotelSidebar
            hotels={hotels}
            selectedHotel={hotelName}
            onSelect={fetchData}
            open={sidebarOpen}
            onClose={() => setSidebarOpen(false)}
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

            <ReviewSubmitForm onSubmitted={() => {
              api.getHotels().then((res) => setHotels(res.data));
              if (hotelName) fetchData(hotelName);
            }} />

            {loading && <p className="status">Loading...</p>}
            {error && <p className="status error">{error}</p>}

            {!hotelName && !loading && (
              <EmptyState
                icon="🏨"
                title="Pick a hotel to get started"
                message="Select a hotel from the sidebar, or submit a review using the form above — it'll appear here once analyzed."
                direction="up"
              />
            )}

            {hotelName && noReviews && !loading && (
              <EmptyState
                icon="📝"
                title="No reviews yet"
                message={`"${hotelName}" doesn't have any analyzed reviews yet. Use the form above to submit one and see it classified in real time.`}
                direction="up"
              />
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
                <SentimentTrendChart data={trend} />
                <ReviewTable reviews={reviews} />
              </>
            )}
          </div>
        </div>
      )}

      {activeTab === 'webhooks' && (
        <div className="layout">
          <div className="dashboard full-width">
            <WebhookManager />
          </div>
        </div>
      )}
    </div>
  );
}

export default App;