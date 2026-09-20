import { useEffect, useState } from 'react';
import {
  apiErrorMessage,
  campaigns,
  deleteCampaign,
  runCampaign,
  stopCampaign,
} from '../services/api';
import { clearActiveCampaignId, getActiveCampaignId, setActiveCampaignId } from '../services/campaign';

export default function Campaigns() {
  const [data, setData] = useState<any[]>([]);
  const [activeId, setActiveId] = useState<number | null>(getActiveCampaignId());
  const [busy, setBusy] = useState<Record<number, string>>({});
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const load = async () => {
    try {
      setData(await campaigns());
    } catch (e) {
      setError(apiErrorMessage(e));
    }
  };

  useEffect(() => {
    void load();
  }, []);

  useEffect(() => {
    const hasRunning = data.some(c => ['running'].includes(c.workflow_status));
    if (!hasRunning) return;
    const timer = window.setInterval(() => void load(), 1500);
    return () => window.clearInterval(timer);
  }, [data]);

  const select = (id: number) => {
    setActiveCampaignId(id);
    setActiveId(id);
    setMessage('Campaign selected.');
    setError('');
  };

  const run = async (campaign: any) => {
    select(campaign.id);
    setBusy(prev => ({ ...prev, [campaign.id]: 'running' }));
    setMessage(`Starting six-agent workflow for ${campaign.product_name}...`);
    setError('');
    try {
      const result = await runCampaign(campaign.id);
      setData(prev => prev.map(x => x.id === campaign.id ? { ...x, workflow_status: result.workflow_status || 'running', status: 'active' } : x));
    } catch (e) {
      setError(apiErrorMessage(e));
    } finally {
      setBusy(prev => ({ ...prev, [campaign.id]: '' }));
    }
  };

  const stop = async (campaign: any) => {
    setBusy(prev => ({ ...prev, [campaign.id]: 'stopping' }));
    setMessage(`Stopping workflow for ${campaign.product_name}...`);
    setError('');
    try {
      const result = await stopCampaign(campaign.id);
      setData(prev => prev.map(x => x.id === campaign.id ? { ...x, workflow_status: result.workflow_status || 'stopped', status: 'stopped' } : x));
      await load();
    } catch (e) {
      setError(apiErrorMessage(e));
    } finally {
      setBusy(prev => ({ ...prev, [campaign.id]: '' }));
    }
  };

  const remove = async (campaign: any) => {
    if (!window.confirm(`Delete campaign "${campaign.product_name}" and all generated content?`)) return;
    setBusy(prev => ({ ...prev, [campaign.id]: 'deleting' }));
    setError('');
    try {
      await deleteCampaign(campaign.id);
      if (activeId === campaign.id) {
        clearActiveCampaignId();
        setActiveId(null);
      }
      setMessage(`${campaign.product_name} deleted.`);
      await load();
    } catch (e) {
      setError(apiErrorMessage(e));
    } finally {
      setBusy(prev => ({ ...prev, [campaign.id]: '' }));
    }
  };

  return <div className="card">
    <div className="row">
      <div>
        <h3>Campaigns</h3>
        <p className="muted">Select one campaign, run or stop its six-agent workflow, or remove it.</p>
      </div>
      <a className="button" href="/create">New campaign</a>
    </div>

    {message && <p className="status">{message}</p>}
    {error && <p className="error">{error}</p>}

    <div className="table-wrap">
      <table>
        <thead><tr><th>Campaign</th><th>Product</th><th>Objective</th><th>Budget</th><th>Status</th><th>Action</th></tr></thead>
        <tbody>
          {data.map(c => {
            const selected = activeId === c.id;
            const running = c.workflow_status === 'running';
            const action = busy[c.id];
            return <tr key={c.id} className={selected ? 'selected-row' : ''}>
              <td><strong>#{data.indexOf(c) + 1}</strong></td>
              <td><strong>{c.product_name}</strong></td>
              <td>{c.objective}</td>
              <td>₹{Number(c.budget).toLocaleString('en-IN')}</td>
              <td><span className={`badge status-${String(c.workflow_status).replace(/_/g, '-')}`}>{c.workflow_status}</span></td>
              <td>
                <div className="action-group">
                  <button className="button secondary" onClick={() => select(c.id)} disabled={selected}>
                    {selected ? 'Selected' : 'Select'}
                  </button>
                  {running
                    ? <button className="button warning" onClick={() => void stop(c)} disabled={action === 'stopping'}>
                        {action === 'stopping' ? 'Stopping…' : 'Stop'}
                      </button>
                    : <button className="button" onClick={() => void run(c)} disabled={!!action}>
                        {action === 'running' ? 'Starting…' : 'Run agents'}
                      </button>}
                  <button className="button danger" onClick={() => void remove(c)} disabled={running || !!action}>
                    {action === 'deleting' ? 'Deleting…' : 'Delete'}
                  </button>
                </div>
              </td>
            </tr>;
          })}
          {!data.length && <tr><td colSpan={6} className="muted">No campaigns yet.</td></tr>}
        </tbody>
      </table>
    </div>
  </div>;
}
