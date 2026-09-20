import { useState } from 'react';
import { getActiveCampaignId } from '../services/campaign';
import { api, apiErrorMessage } from '../services/api';

export default function Strategy() {
  const active = getActiveCampaignId();
  const [id, setId] = useState(active ? String(active) : '');
  const [s, setS] = useState<any>();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const load = async () => {
    if (!id || Number(id) < 1) return setError('Enter a valid campaign ID.');
    setLoading(true); setError('');
    try { setS((await api.get(`/api/campaigns/${Number(id)}/strategy`)).data); }
    catch (e) { setError(apiErrorMessage(e)); }
    finally { setLoading(false); }
  };

  if (!active && !id) return <div className="card"><h3>Select a campaign first</h3><p className="muted">Go to Campaigns, select a campaign, then return here.</p></div>;
  return <div className="card">
    <h3>Campaign strategy</h3>
    <label>Campaign ID</label><input value={id} onChange={e => setId(e.target.value)} />
    <button className="button" onClick={() => void load()} disabled={loading}>{loading ? 'Loading…' : 'Generate / view strategy'}</button>
    {error && <p className="error">{error}</p>}
    {s && <div className="grid" style={{ marginTop: 18 }}>
      <div className="card"><b>Theme</b><p>{s.theme}</p></div>
      <div className="card"><b>Objectives</b><p>{s.objectives?.join(', ')}</p></div>
      <div className="card"><b>Audience</b><p>{s.audience_segments?.map((x: any) => x.name).join(', ')}</p></div>
      <div className="card"><b>Channels</b><p>{s.channels?.join(', ')}</p></div>
      <div className="card"><b>Timeline</b><p>{s.timeline_days} days</p></div>
      <div className="card"><b>KPIs</b><p>{s.kpis?.join(', ')}</p></div>
      <div className="card"><b>Budget allocation</b><pre>{JSON.stringify(s.budget_allocation, null, 2)}</pre></div>
    </div>}
  </div>;
}
