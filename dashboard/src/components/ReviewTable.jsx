export default function ReviewTable({ reviews }) {
  return (
    <div className="table-box">
      <h3>Recent Reviews</h3>
      <table>
        <thead>
          <tr>
            <th>Review</th>
            <th>Sentiment</th>
            <th>Confidence</th>
            <th>Model</th>
            <th>Date</th>
          </tr>
        </thead>
        <tbody>
          {reviews.map((review) => (
            <tr key={review.id}>
              <td className="review-text">{review.body.slice(0, 80)}...</td>
              <td>
                <span className={`badge sentiment-${review.sentiment?.label}`}>
                  {review.sentiment?.label || 'pending'}
                </span>
              </td>
              <td>{review.sentiment ? `${(review.sentiment.confidence * 100).toFixed(0)}%` : '—'}</td>
              <td>{review.sentiment?.model_used || '—'}</td>
              <td>{new Date(review.created_at).toLocaleDateString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}