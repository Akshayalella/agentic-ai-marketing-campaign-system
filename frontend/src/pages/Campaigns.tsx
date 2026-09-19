import { useEffect, useState } from 'react';
import { campaigns, runCampaign } from '../services/api';
import { setActiveCampaignId } from '../services/campaign';

export default function Campaigns() {
  const [data, setData] = useState<any[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [message, setMessage] = useState('');

  const load = () => {
    campaigns()
      .then(setData)
      .catch(() => {});
  };

  useEffect(() => {
    load();
  }, []);

  const handleSelect = (id: number) => {
    setActiveCampaignId(id);
    setSelectedId(id);
    setMessage(`Campaign #${id} selected.`);
  };

  const handleRun = async (id: number) => {
    const campaign = data.find((c) => c.id === id);

    if (
      campaign &&
      campaign.workflow_status &&
      campaign.workflow_status !== 'not_started'
    ) {
      setMessage(
        `Campaign #${id} is already at "${campaign.workflow_status}". Agents will not be rerun.`
      );
      return;
    }

    try {
      setActiveCampaignId(id);
      setMessage(`Running agents for Campaign #${id}...`);
      await runCampaign(id);
      setMessage(`Campaign #${id} agents completed.`);
      load();
    } catch {
      setMessage(`Failed to run agents for Campaign #${id}.`);
    }
  };

  return (
    <div className="card">
      <div className="row">
        <h3>Campaigns</h3>
        <a className="button" href="/create">
          New campaign
        </a>
      </div>

      {message && <p className="status">{message}</p>}

      <table>
        <thead>
          <tr>
            <th>Product</th>
            <th>Objective</th>
            <th>Budget</th>
            <th>Status</th>
            <th>Action</th>
          </tr>
        </thead>

        <tbody>
          {data.map((c) => (
            <tr key={c.id}>
              <td>{c.product_name}</td>
              <td>{c.objective}</td>
              <td>₹{c.budget}</td>
              <td>{c.workflow_status}</td>

              <td>
                <button
                  className="button secondary"
                  onClick={() => handleSelect(c.id)}
                >
                  {selectedId === c.id ? 'Selected' : 'Select'}
                </button>{' '}

                <button
                  className="button"
                  onClick={() => handleRun(c.id)}
                  disabled={
                    c.workflow_status &&
                    c.workflow_status !== 'not_started'
                  }
                >
                  {c.workflow_status &&
                  c.workflow_status !== 'not_started'
                    ? 'Already processed'
                    : 'Run agents'}
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}