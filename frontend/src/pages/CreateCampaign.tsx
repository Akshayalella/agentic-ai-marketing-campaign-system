import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { apiErrorMessage, createCampaign, runCampaign } from '../services/api';
import { setActiveCampaignId } from '../services/campaign';

const AVAILABLE_PLATFORMS = ['LinkedIn', 'Email', 'Instagram'];

export default function CreateCampaign() {
  const navigate = useNavigate();
  const [f, setF] = useState<any>({
    product_name: '',
    description: '',
    target_audience: '',
    objective: 'Generate qualified leads',
    budget: 50000,
    duration_days: 30,
    platforms: ['LinkedIn', 'Email', 'Instagram'],
    brand_tone: 'Professional',
    brand_guidelines: '',
  });
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const update = (key: string, value: any) => setF((prev: any) => ({ ...prev, [key]: value }));
  const togglePlatform = (platform: string) => {
    const exists = f.platforms.includes(platform);
    const next = exists ? f.platforms.filter((x: string) => x !== platform) : [...f.platforms, platform];
    update('platforms', next);
  };

  const submit = async (e: any) => {
    e.preventDefault();
    setError('');
    setMessage('');
    if (!f.product_name.trim()) return setError('Product name is required.');
    if (!f.target_audience.trim()) return setError('Target audience is required.');
    if (!f.platforms.length) return setError('Select at least one platform.');
    if (Number(f.budget) < 0 || Number(f.duration_days) < 1) return setError('Budget and duration must be valid.');

    setSubmitting(true);
    try {
      const c = await createCampaign({ ...f, product_name: f.product_name.trim(), target_audience: f.target_audience.trim() });
      setActiveCampaignId(c.id);
      await runCampaign(c.id);
      setMessage(`Campaign #${c.id} created. Six-agent workflow is running in the background.`);
    } catch (e) {
      setError(apiErrorMessage(e));
    } finally {
      setSubmitting(false);
    }
  };

  return <form className="card" onSubmit={submit}>
    <div className="row">
      <div><h3>Campaign requirements</h3><p className="muted">Provide the product, audience, objective, budget, channels and brand rules.</p></div>
      <Link className="button secondary" to="/campaigns">View campaigns</Link>
    </div>

    {[['product_name', 'Product name'], ['description', 'Product description'], ['target_audience', 'Target audience'], ['objective', 'Marketing objective'], ['brand_guidelines', 'Brand guidelines']].map(([k, l]) =>
      <div key={k}><label>{l}</label>{k === 'description' || k === 'brand_guidelines'
        ? <textarea value={f[k]} onChange={e => update(k, e.target.value)} rows={k === 'brand_guidelines' ? 5 : 3} />
        : <input value={f[k]} onChange={e => update(k, e.target.value)} />}</div>
    )}

    <div className="grid2">
      <div><label>Budget (₹)</label><input type="number" min="0" value={f.budget} onChange={e => update('budget', Number(e.target.value))} /></div>
      <div><label>Duration (days)</label><input type="number" min="1" max="365" value={f.duration_days} onChange={e => update('duration_days', Number(e.target.value))} /></div>
    </div>

    <label>Platforms</label>
    <div className="platform-grid">
      {AVAILABLE_PLATFORMS.map(platform => <label className="check-card" key={platform}>
        <input type="checkbox" checked={f.platforms.includes(platform)} onChange={() => togglePlatform(platform)} />
        <span>{platform}</span>
      </label>)}
    </div>

    <label>Brand tone</label>
    <input value={f.brand_tone} onChange={e => update('brand_tone', e.target.value)} />

    <button className="button" disabled={submitting}>{submitting ? 'Creating…' : 'Create & run six-agent workflow'}</button>
    {message && <p className="status">{message} <button type="button" className="link-button" onClick={() => navigate('/campaigns')}>Open campaigns</button></p>}
    {error && <p className="error">{error}</p>}
  </form>;
}
