export default function ActionLog({ actions }) {
  return (
    <div className="action-log-container">
      <h3>📋 Action Log</h3>
      <div className="action-log">
        {actions.length === 0 ? (
          <div className="empty-log">No actions yet</div>
        ) : (
          actions.map((action, idx) => (
            <div key={idx} className="action-log-item">
              {action}
            </div>
          ))
        )}
      </div>
    </div>
  )
}
