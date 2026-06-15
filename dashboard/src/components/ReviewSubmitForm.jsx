import { useState } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';

const API_BASE = 'http://localhost:8000/api/v1';

export default function ReviewSubmitForm({ onSubmitted }) {
  const [hotelName, setHotelName] = useState('');
  const [body, setBody] = useState('');
  const [rating, setRating] = useState('');
  const [status, setStatus] = useState('idle'); // idle | submitting | polling | done | error
  const [result, setResult] = useState(null);

  const pollForResult = async (reviewId, attempts = 0) => {
    if (attempts > 10) {
      setStatus('error');
      return;
    }
    try {
      const res = await axios.get(`${API_BASE}/reviews/${reviewId}/`);
      if (res.data.status === 'done') {
        setResult(res.data);
        setStatus('done');
        toast.success(`Classified as ${res.data.sentiment.label}!`);

      } else {
        setTimeout(() => pollForResult(reviewId, attempts + 1), 1500);
      }
    } catch {
      setStatus('error');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!hotelName.trim() || !body.trim()) return;

    setStatus('submitting');
    setResult(null);

    try {
      const payload = { hotel_name: hotelName, body, language: 'en' };
      if (rating) payload.rating = parseFloat(rating);

      const res = await axios.post(`${API_BASE}/reviews/submit/`, payload);
      setStatus('polling');
      toast.success('Review submitted — analyzing...');
      pollForResult(res.data.id);
    } catch {
      setStatus('error');
      toast.error('Failed to submit review.');

    }
  };

  const reset = () => {
    setHotelName('');
    setBody('');
    setRating('');
    setStatus('idle');
    setResult(null);
    if (onSubmitted) onSubmitted();
  };

  return (
    <div className="submit-form">
      <h3>Submit a Review</h3>

      {status !== 'done' && (
        <form onSubmit={handleSubmit}>
          <input
            type="text"
            placeholder="Hotel name"
            value={hotelName}
            onChange={(e) => setHotelName(e.target.value)}
            disabled={status === 'submitting' || status === 'polling'}
          />
          <textarea
            placeholder="Write your review..."
            value={body}
            onChange={(e) => setBody(e.target.value)}
            rows={4}
            disabled={status === 'submitting' || status === 'polling'}
          />
          <input
            type="number"
            step="0.1"
            min="0"
            max="5"
            placeholder="Rating (optional, 0-5)"
            value={rating}
            onChange={(e) => setRating(e.target.value)}
            disabled={status === 'submitting' || status === 'polling'}
          />
          <button type="submit" disabled={status === 'submitting' || status === 'polling'}>
            {status === 'submitting' && 'Submitting...'}
            {status === 'polling' && 'Analyzing sentiment...'}
            {(status === 'idle' || status === 'error') && 'Submit Review'}
          </button>
        </form>
      )}

      {status === 'error' && (
        <p className="status error">Something went wrong. Please try again.</p>
      )}

      {status === 'done' && result && (
        <div className="result-card">
          <p className="result-label">Analysis complete</p>
          <div className={`badge sentiment-${result.sentiment.label}`}>
            {result.sentiment.label} · {(result.sentiment.confidence * 100).toFixed(0)}% confidence
          </div>
          <p className="result-model">Model used: {result.sentiment.model_used}</p>

          {result.aspects.length > 0 && (
            <div className="result-aspects">
              {result.aspects.map((a) => (
                <span key={a.category} className={`badge sentiment-${a.label}`}>
                  {a.category}: {a.label}
                </span>
              ))}
            </div>
          )}

          <button onClick={reset}>Submit another</button>
        </div>
      )}
    </div>
  );
}