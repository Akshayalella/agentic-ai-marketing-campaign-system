import { useEffect, useState } from 'react';
import { getActiveCampaignId, getCampaignDisplayNumber, setActiveCampaignId } from '../services/campaign';
import { api, apiErrorMessage, campaigns } from '../services/api';

export default function Research() {
  const [campaignList, setCampaignList] = useState<any[]>([]);
  const [id, setId] = useState<number | null>(getActiveCampaignId());
  const [r, setR] = useState<any>();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const loadCampaigns = async () => {
    try {
      const list = await campaigns();
      setCampaignList(list);
      const stored = getActiveCampaignId();
      const selected = list.find((c: any) => Number(c.id) === Number(stored))?.id ?? list[0]?.id ?? null;
      setId(selected);
      if (selected) setActiveCampaignId(Number(selected));
    } catch (e) {
      setError(apiErrorMessage(e));
    }
  };

  const load = async () => {
    if (!id) return setError('Select a campaign first.');
    setLoading(true); setError('');
    try { setR((await api.get(`/api/campaigns/${Number(id)}/research`, { params: { _: Date.now() } })).data); }
    catch (e) { setError(apiErrorMessage(e)); }
    finally { setLoading(false); }
  };

  useEffect(() => { void loadCampaigns(); }, []);
  useEffect(() => { if (id) void load(); }, [id]);

  if (!campaignList.length) return <div className="card"><h3>No campaigns yet</h3><p className="muted">Create a campaign first, then return here.</p></div>;
  const displayNumber = getCampaignDisplayNumber(campaignList, id) ?? 1;
  const selected = campaignList.find((c: any) => Number(c.id) === Number(id));

  return <div className="card">
    <h3>Audience & competitor research · Campaign #{displayNumber}</h3>
    <p className="muted">Selected campaign: {selected?.product_name || '—'}</p>
    <label>Campaign</label>
    <select value={id ?? ''} onChange={e => { const value = Number(e.target.value); setId(value); setActiveCampaignId(value); }}>
      {campaignList.map((c: any, index: number) => <option key={c.id} value={c.id}>Campaign #{index + 1} · {c.product_name}</option>)}
    </select>
    <button className="button" onClick={() => void load()} disabled={loading}>{loading ? 'Loading…' : 'Refresh research'}</button>
    {error && <p className="error">{error}</p>}
    {r && <div>
      <h4>Audience personas</h4>
      {r.personas?.map((p: any) => <div className="card compact" key={p.name}><b>{p.name}</b><p className="muted">{p.description} · {p.verified ? 'Verified' : 'Hypothetical'}</p></div>)}
      <h4>Sources</h4>
      {r.sources?.map((s: any, i: number) => <div className="card compact" key={`${s.url}-${i}`}><b>{s.title}</b><p>{s.summary}</p><a href={s.url} target="_blank" rel="noreferrer">Open source</a><p className="muted">Source type: {s.source_type || 'unknown'}</p></div>)}
    </div>}
  </div>;
}
