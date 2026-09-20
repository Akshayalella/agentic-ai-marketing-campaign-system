import { useEffect, useState } from 'react';
import { analytics, analyticsUpload, apiErrorMessage, report } from '../services/api';
import { getActiveCampaignId } from '../services/campaign';

const emptyTargets = { engagement_rate: '', ctr: '', conversion_rate: '', cost_per_lead: '' };

export default function Analytics() {
  const id = getActiveCampaignId();
  const [r, setR] = useState<any>();
  const [targets, setTargets] = useState(emptyTargets);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!id) return;
    report(id).then(data => setR(data.analytics)).catch(() => {});
  }, [id]);

  if (!id) return <div className="card"><h3>Select a campaign first</h3><p className="muted">Go to Campaigns and select a campaign.</p></div>;

  const targetValues = () => Object.fromEntries(
    Object.entries(targets).filter(([, v]) => v !== '').map(([k, v]) => [k, Number(v)])
  ) as Record<string, number>;

  const run = async () => {
    setLoading(true); setError('');
    try {
      setR(await analytics(id, {
        impressions: 10000, engagements: 700, clicks: 400, conversions: 45,
        spending: 12000, leads: 45, observed: false, targets: targetValues()
      }));
    } catch (e) { setError(apiErrorMessage(e)); }
    finally { setLoading(false); }
  };

  const upload = async (e: any) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setLoading(true); setError('');
    try { setR(await analyticsUpload(id, file, targetValues())); }
    catch (err) { setError(apiErrorMessage(err)); }
    finally { setLoading(false); e.target.value = ''; }
  };

  return <div className="card">
    <h3>Campaign analytics · #{id}</h3>
    <p className="muted">Projected and observed metrics are stored separately. The performance score is calculated from engagement, CTR, conversion rate and CPL against transparent benchmark/target values.</p>

    <div className="grid2">
      {([
        ['engagement_rate', 'Engagement target (%)'], ['ctr', 'CTR target (%)'],
        ['conversion_rate', 'Conversion target (%)'], ['cost_per_lead', 'CPL target (₹)']
      ] as const).map(([k, l]) => <div key={k}>
        <label>{l}</label>
        <input type="number" min="0" value={targets[k]} onChange={e => setTargets({ ...targets, [k]: e.target.value })} />
      </div>)}
    </div>

    <div className="row" style={{ marginTop: 15 }}>
      <button className="button" onClick={() => void run()} disabled={loading}>{loading ? 'Calculating…' : 'Calculate projected KPIs'}</button>
      <label className="button secondary">Upload observed CSV<input type="file" accept=".csv" hidden onChange={upload} disabled={loading} /></label>
    </div>
    {error && <p className="error">{error}</p>}

    {r && <>
      <div className="grid" style={{ marginTop: 18 }}>
        {[
          ['Data type', r.observed ? 'Observed' : 'Projected'],
          ['Performance score', `${r.performance_score}/100`],
          ['Engagement rate', `${Number(r.engagement_rate).toFixed(2)}%`],
          ['CTR', `${Number(r.ctr).toFixed(2)}%`],
          ['Conversion rate', `${Number(r.conversion_rate).toFixed(2)}%`],
          ['Cost per lead', `₹${Number(r.cost_per_lead).toFixed(2)}`],
          ['Spending', `₹${Number(r.spending).toLocaleString('en-IN', { maximumFractionDigits: 2 })}`]
        ].map(([a, b]) => <div className="card" key={a}><div className="muted">{a}</div><div className="big">{b}</div></div>)}
      </div>

      {r.target_comparison && <div className="card" style={{ marginTop: 18 }}>
        <h4>Target comparison</h4>
        {Object.entries(r.target_comparison).map(([k, v]: any) => <p key={k}>{k}: {Number(v.actual).toFixed(2)} vs {Number(v.target).toFixed(2)} — <b>{String(v.status).replace(/_/g, ' ')}</b></p>)}
      </div>}

      {r.trends && <div className="card" style={{ marginTop: 18 }}>
        <h4>Previous-period trends</h4>
        {Object.entries(r.trends).map(([k, v]: any) => <p key={k}>{k}: {Number(v.change).toFixed(2)} change {v.change_percent == null ? '' : `(${Number(v.change_percent).toFixed(1)}%)`}</p>)}
      </div>}

      {r.improvement_suggestions && <div className="card" style={{ marginTop: 18 }}>
        <h4>Improvement suggestions</h4>
        <ul>{r.improvement_suggestions.map((s: string, i: number) => <li key={i}>{s}</li>)}</ul>
      </div>}
    </>}
  </div>;
}
