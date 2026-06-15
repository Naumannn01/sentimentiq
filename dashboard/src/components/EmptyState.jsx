export default function EmptyState({ icon = '👋', title, message, direction }) {
  return (
    <div className="empty-state">
      {direction === 'up' && <div className="empty-arrow up">↑</div>}
      <div className="empty-icon">{icon}</div>
      <h3>{title}</h3>
      <p>{message}</p>
    </div>
  );
}