import { useState } from 'react';
import { getActiveCampaignId } from '../services/campaign';
import { api, apiErrorMessage } from '../services/api';

export default function Research() {
  const active = getActiveCampaignId();
  const [id, setId] = useState(active ? String(active) : '');
  const [r, setR] = useState<any>();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const load = async () => {
    if (!id || Number(id) < 1) return setError('Enter a valid campaign ID.');
    setLoading(true); setError('');
    try { setR((await api.get(`/api/campaigns/${Number(id)}/research`)).data); }
    catch (e) { setError(apiErrorMessage(e)); }
    finally { setLoading(false); }
  };

  if (!active && !id) return <div className="card"><h3>Select a campaign first</h3><p className="muted">Go to Campaigns, select a campaign, then return here.</p></div>;
  return <div className="card">
    <h3>Audience & competitor research</h3>
    <label>Campaign ID</label><input value={id} onChange={e => setId(e.target.value)} />
    <button className="button" onClick={() => void load()} disabled={loading}>{loading ? 'Loading…' : 'Load research'}</button>
    {error && <p className="error">{error}</p>}
    {r && <div>
      <h4>Audience personas</h4>
      {r.personas?.map((p: any) => <div className="card compact" key={p.name}><b>{p.name}</b><p className="muted">{p.description} · {p.verified ? 'Verified' : 'Hypothetical'}</p></div>)}
      <h4>Sources</h4>
      {r.sources?.map((s: any, i: number) => <div className="card compact" key={`${s.url}-${i}`}><b>{s.title}</b><p>{s.summary}</p><a href={s.url} target="_blank" rel="noreferrer">Open source</a><p className="muted">Source type: {s.source_type || 'unknown'}</p></div>)}
    </div>}
  </div>;
}
