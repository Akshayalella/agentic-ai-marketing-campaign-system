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
      .catch(() => {
        setMessage('Failed to load campaigns.');
      });
  };

  useEffect(() => {
    load();
  }, []);

  const handleSelect = (id: number) => {
    setActiveCampaignId(id);
    setSelectedId(id);
    setMessage(`Campaign #${id} selected.`);
  };

  const handleRun = async (id: number, status: string) => {
    if (status !== 'not_started') {
      setMessage(`Campaign #${id} has already been processed.`);
      return;
    }

    try {
      setMessage(`Running six-agent workflow for Campaign #${id}...`);
      setActiveCampaignId(id);
      setSelectedId(id);

      await runCampaign(id);

      setMessage(`Campaign #${id} workflow completed.`);
      load();
    } catch {
      setMessage(`Failed to run Campaign #${id}.`);
    }
  };

  const handleDelete = async (id: number) => {
    const campaign = data.find((c) => c.id === id);

    const confirmed = window.confirm(
      `Are you sure you want to delete Campaign #${id}${
        campaign?.product_name ? ` (${campaign.product_name})` : ''
      }?\n\nThis will permanently delete the campaign and its generated content.`
    );

    if (!confirmed) {
      return;
    }

    try {
      setMessage(`Deleting Campaign #${id}...`);

      const response = await fetch(
        `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api/campaigns/${id}`,
        {
          method: 'DELETE',
        }
      );

      if (!response.ok) {
        throw new Error('Delete failed');
      }

      if (selectedId === id) {
        setSelectedId(null);
      }

      setMessage(`Campaign #${id} deleted successfully.`);
      load();
    } catch {
      setMessage(`Failed to delete Campaign #${id}.`);
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

      {message && (
        <p
          style={{
            marginTop: '12px',
            marginBottom: '12px',
          }}
        >
          {message}
        </p>
      )}

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
                  disabled={c.workflow_status !== 'not_started'}
                  onClick={() =>
                    handleRun(c.id, c.workflow_status)
                  }
                >
                  {c.workflow_status === 'not_started'
                    ? 'Run agents'
                    : 'Already processed'}
                </button>{' '}

                <button
                  className="button secondary"
                  onClick={() => handleDelete(c.id)}
                >
                  Delete
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}