import { useEffect, useMemo, useState } from 'react';
import { apiErrorMessage, campaigns } from '../services/api';

export default function Dashboard() {
  const [data, setData] = useState<any[]>([]);
  const [error, setError] = useState('');

  const load = async () => {
    try {
      setData(await campaigns());
      setError('');
    } catch (e) {
      setError(apiErrorMessage(e));
    }
  };

  useEffect(() => {
    void load();
    const timer = window.setInterval(() => void load(), 1000);
    return () => window.clearInterval(timer);
  }, []);

  const active = useMemo(() => data.filter(x => x.status === 'active'), [data]);
  const running = useMemo(() => data.filter(x => x.workflow_status === 'running'), [data]);

  return <>
    <div className="hero">
      <div className="row">
        <div>
          <h2>AI-powered campaign operations</h2>
          <p className="muted">Run the six-agent workflow from requirements to approved content and measurable campaign reports.</p>
        </div>
        <button className="button secondary" onClick={() => void load()}>Refresh</button>
      </div>
    </div>
    {error && <p className="error">{error}</p>}

    <div className="grid">
      <div className="card">
        <div className="muted">All campaigns</div>
        <div className="big">{data.length}</div>
      </div>
      <div className="card">
        <div className="muted">Active campaigns</div>
        <div className="big">{active.length}</div>
        <div className="muted">Campaigns started for execution</div>
      </div>
      <div className="card">
        <div className="muted">Running workflows</div>
        <div className="big">{running.length}</div>
        <div className="muted">Six-agent workflows executing now</div>
      </div>
    </div>

    <div className="grid2" style={{ marginTop: 18 }}>
      <div className="card">
        <h3>Active campaigns</h3>
        {active.length ? <div className="compact-list">{active.map(c => <div className="compact-row" key={c.id}>
          <strong>#{data.indexOf(c) + 1} · {c.product_name}</strong>
          <span className="badge status-active">{c.workflow_status}</span>
        </div>)}</div> : <p className="muted">No active campaigns. Create a campaign and run its agents.</p>}
      </div>
      <div className="card">
        <h3>All campaigns</h3>
        {data.length ? <div className="compact-list">{data.map((c, index) => <div className="compact-row" key={c.id}>
          <strong>#{index + 1} · {c.product_name}</strong>
          <span className={`badge status-${String(c.workflow_status).replace(/_/g, '-')}`}></span>
          <span className="muted">{c.workflow_status}</span>
        </div>)}</div> : <p className="muted">No campaigns yet.</p>}
      </div>
    </div>

    <div className="card" style={{ marginTop: 18 }}>
      <h3>Six-agent pipeline</h3>
      <p className="muted">Requirements → Research → Strategy → Content → Compliance → Analytics → Human Approval → Calendar / Publishing</p>
      <p className="muted">Active campaigns start at <b>0</b>. Clicking <b>Run agents</b> changes Active campaigns to <b>1</b>; while the workflow is executing, Running workflows becomes <b>1</b>.</p>
    </div>
  </>;
}
