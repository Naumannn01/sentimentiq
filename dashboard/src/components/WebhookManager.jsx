import { useState, useEffect } from 'react';
import { api } from '../api';
import toast from 'react-hot-toast';


export default function WebhookManager() {
  const [webhooks, setWebhooks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expandedId, setExpandedId] = useState(null);
  const [logs, setLogs] = useState({});
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const [form, setForm] = useState({
    name: '',
    target_url: '',
    hotel_name: '',
    event: 'review.done',
    secret: '',
  });

  const loadWebhooks = async () => {
    setLoading(true);
    try {
      const res = await api.getWebhooks();
      setWebhooks(res.data.results || res.data);
    } catch {
      setError('Failed to load webhooks.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadWebhooks();
  }, []);

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.name.trim() || !form.target_url.trim()) return;
    setSubmitting(true);
    try {
      const payload = { ...form };
      if (!payload.secret) delete payload.secret;
      await api.createWebhook(payload);
      setForm({ name: '', target_url: '', hotel_name: '', event: 'review.done', secret: '' });
      setShowForm(false);
      toast.success('Webhook registered!');
      loadWebhooks();
    } catch {
      toast.error('Failed to register webhook — check the URL.');
    } finally {
      setSubmitting(false);
    }
  };

  const toggleActive = async (wh) => {
    try {
      await api.updateWebhook(wh.id, { is_active: !wh.is_active });
      toast.success(wh.is_active ? 'Webhook disabled' : 'Webhook enabled');
      loadWebhooks();
    } catch {
      toast.error('Failed to update webhook.');
    }
  };

  const handleDelete = async (id) => {
    if (!confirm('Delete this webhook subscription?')) return;
    try {
      await api.deleteWebhook(id);
      toast.success('Webhook deleted');
      loadWebhooks();
    } catch {
      toast.error('Failed to delete webhook.');
    }
  };


  const toggleLogs = async (id) => {
    if (expandedId === id) {
      setExpandedId(null);
      return;
    }
    setExpandedId(id);
    if (!logs[id]) {
      try {
        const res = await api.getWebhookLogs(id);
        setLogs((prev) => ({ ...prev, [id]: res.data.results || res.data }));
      } catch {
        setLogs((prev) => ({ ...prev, [id]: [] }));
      }
    }
  };

  return (
    <div className="webhook-page">
      <div className="webhook-header">
        <div>
          <h2>Webhook Subscriptions</h2>
          <p className="subtle">
            Get notified the moment a review finishes processing — sentiment,
            confidence, and aspect breakdown pushed to your URL.
          </p>
        </div>
        <button className="primary" onClick={() => setShowForm(!showForm)}>
          {showForm ? 'Cancel' : '+ New Webhook'}
        </button>
      </div>

      {error && <p className="status error">{error}</p>}

      {showForm && (
        <form className="webhook-form" onSubmit={handleSubmit}>
          <div className="form-row">
            <label>Name</label>
            <input name="name" placeholder="e.g. Hotel PMS Integration"
              value={form.name} onChange={handleChange} />
          </div>
          <div className="form-row">
            <label>Target URL</label>
            <input name="target_url" placeholder="https://webhook.site/your-url"
              value={form.target_url} onChange={handleChange} />
          </div>
          <div className="form-row">
            <label>Hotel filter (optional)</label>
            <input name="hotel_name" placeholder="Leave blank for all hotels"
              value={form.hotel_name} onChange={handleChange} />
          </div>
          <div className="form-row">
            <label>Event</label>
            <select name="event" value={form.event} onChange={handleChange}>
              <option value="review.done">review.done</option>
              <option value="sentiment.drop">sentiment.drop</option>
            </select>
          </div>
          <div className="form-row">
            <label>Secret (optional)</label>
            <input name="secret" placeholder="Used to sign payloads with HMAC"
              value={form.secret} onChange={handleChange} />
          </div>
          <button type="submit" className="primary" disabled={submitting}>
            {submitting ? 'Registering...' : 'Register Webhook'}
          </button>
        </form>
      )}

      {loading ? (
        <p className="status">Loading webhooks...</p>
      ) : webhooks.length === 0 ? (
        <p className="status">No webhooks registered yet.</p>
      ) : (
        <div className="webhook-list">
          {webhooks.map((wh) => (
            <div className="webhook-card" key={wh.id}>
              <div className="webhook-row">
                <div className="webhook-info">
                  <div className="webhook-name">
                    {wh.name}
                    <span className={`badge ${wh.is_active ? 'sentiment-positive' : 'sentiment-negative'}`}>
                      {wh.is_active ? 'active' : 'inactive'}
                    </span>
                  </div>
                  <div className="webhook-url">{wh.target_url}</div>
                  <div className="webhook-meta">
                    Event: <code>{wh.event}</code>
                    {wh.hotel_name && <> · Hotel: <code>{wh.hotel_name}</code></>}
                  </div>
                </div>
                <div className="webhook-actions">
                  <button onClick={() => toggleLogs(wh.id)}>
                    {expandedId === wh.id ? 'Hide logs' : 'View logs'}
                  </button>
                  <button onClick={() => toggleActive(wh)}>
                    {wh.is_active ? 'Disable' : 'Enable'}
                  </button>
                  <button className="danger" onClick={() => handleDelete(wh.id)}>
                    Delete
                  </button>
                </div>
              </div>

              {expandedId === wh.id && (
                <div className="webhook-logs">
                  {!logs[wh.id] ? (
                    <p className="status">Loading logs...</p>
                  ) : logs[wh.id].length === 0 ? (
                    <p className="status">No deliveries yet — submit a review to trigger this webhook.</p>
                  ) : (
                    <table>
                      <thead>
                        <tr>
                          <th>Result</th>
                          <th>Status code</th>
                          <th>Fired at</th>
                          <th>Response</th>
                        </tr>
                      </thead>
                      <tbody>
                        {logs[wh.id].map((log) => (
                          <tr key={log.id}>
                            <td>
                              <span className={`badge ${log.result === 'success' ? 'sentiment-positive' : 'sentiment-negative'}`}>
                                {log.result}
                              </span>
                            </td>
                            <td>{log.status_code ?? '—'}</td>
                            <td>{new Date(log.fired_at).toLocaleString()}</td>
                            <td className="log-response">{(log.response || '—').slice(0, 60)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}