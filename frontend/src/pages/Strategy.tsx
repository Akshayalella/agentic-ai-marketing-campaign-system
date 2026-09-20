import { useEffect, useState } from 'react';
import { getActiveCampaignId, getCampaignDisplayNumber, setActiveCampaignId } from '../services/campaign';
import { api, apiErrorMessage, campaigns } from '../services/api';

export default function Strategy() {
  const [campaignList, setCampaignList] = useState<any[]>([]);
  const [id, setId] = useState<number | null>(getActiveCampaignId());
  const [s, setS] = useState<any>();
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
    try { setS((await api.get(`/api/campaigns/${Number(id)}/strategy`, { params: { _: Date.now() } })).data); }
    catch (e) { setError(apiErrorMessage(e)); }
    finally { setLoading(false); }
  };

  useEffect(() => { void loadCampaigns(); }, []);
  useEffect(() => { if (id) void load(); }, [id]);

  if (!campaignList.length) return <div className="card"><h3>No campaigns yet</h3><p className="muted">Create a campaign first, then return here.</p></div>;
  const displayNumber = getCampaignDisplayNumber(campaignList, id) ?? 1;
  const selected = campaignList.find((c: any) => Number(c.id) === Number(id));

  return <div className="card">
    <h3>Campaign strategy · Campaign #{displayNumber}</h3>
    <p className="muted">Selected campaign: {selected?.product_name || '—'}</p>
    <label>Campaign</label>
    <select value={id ?? ''} onChange={e => { const value = Number(e.target.value); setId(value); setActiveCampaignId(value); }}>
      {campaignList.map((c: any, index: number) => <option key={c.id} value={c.id}>Campaign #{index + 1} · {c.product_name}</option>)}
    </select>
    <button className="button" onClick={() => void load()} disabled={loading}>{loading ? 'Loading…' : 'Refresh strategy'}</button>
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
