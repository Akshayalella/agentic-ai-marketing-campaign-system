import { useEffect, useState } from 'react';
import { apiErrorMessage, campaigns } from '../services/api';

export default function Dashboard() {
  const [data, setData] = useState<any[]>([]);
  const [error, setError] = useState('');

  useEffect(() => {
    campaigns().then(setData).catch(e => setError(apiErrorMessage(e)));
  }, []);

  return <>
    <div className="hero"><h2>AI-powered campaign operations</h2><p className="muted">Run the six-agent workflow from requirements to approved content and measurable campaign reports.</p></div>
    {error && <p className="error">{error}</p>}
    <div className="grid">
      <div className="card"><div className="muted">Campaigns</div><div className="big">{data.length}</div></div>
      <div className="card"><div className="muted">Active</div><div className="big">{data.filter(x => x.status === 'active').length}</div></div>
      <div className="card"><div className="muted">Running workflows</div><div className="big">{data.filter(x => x.workflow_status === 'running').length}</div></div>
    </div>
    <div className="card" style={{ marginTop: 18 }}><h3>Six-agent pipeline</h3><p className="muted">Requirements → Research → Strategy → Content → Compliance → Analytics → Human Approval → Calendar / Publishing</p></div>
  </>;
}
