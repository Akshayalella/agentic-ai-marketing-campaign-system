import { useEffect, useState } from 'react';
import { apiErrorMessage, approve, campaigns, content, editContent, publish, regenerate, reject } from '../services/api';
import { getActiveCampaignId, getCampaignDisplayNumber } from '../services/campaign';

export default function ContentStudio() {
  const id = getActiveCampaignId();
  const [items, setItems] = useState<any[]>([]);
  const [editing, setEditing] = useState<Record<number, string>>({});
  const [working, setWorking] = useState<Record<number, string>>({});
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [campaignList, setCampaignList] = useState<any[]>([]);

  const load = async () => {
    if (!id) return;
    try {
      const [contentItems, allCampaigns] = await Promise.all([content(id), campaigns()]);
      setItems(contentItems);
      setCampaignList(allCampaigns);
    }
    catch (e) { setError(apiErrorMessage(e)); }
  };

  useEffect(() => { void load(); }, [id]);

  const action = async (item: any, name: string, fn: () => Promise<any>) => {
    setWorking(prev => ({ ...prev, [item.id]: name })); setError(''); setMessage('');
    try {
      const result = await fn();
      setMessage(`${name} completed for ${item.platform}.`);
      if (result?.content?.id) {
        setItems(prev => prev.map(existing =>
          existing.id === result.content.id ? result.content : existing
        ));
      } else {
        await load();
      }
    } catch (e) { setError(apiErrorMessage(e)); }
    finally { setWorking(prev => ({ ...prev, [item.id]: '' })); }
  };

  if (!id) return <div className="card"><h3>Select a campaign first</h3><p className="muted">Go to Campaigns and select a campaign.</p></div>;

  return <>
    <div className="hero">
      <div className="row"><div><h2>Content Studio · Campaign #{getCampaignDisplayNumber(campaignList, id) ?? 1}</h2><p className="muted">Edit, review, approve or regenerate AI-generated content. Publishing requires human approval.</p></div><button className="button secondary" onClick={() => void load()}>Refresh</button></div>
    </div>
    {message && <p className="status">{message}</p>}
    {error && <p className="error">{error}</p>}
    <div className="grid2">
      {items.map(x => {
        const busy = working[x.id];
        const reviewerPass = ['approved_for_human_review', 'passed', 'approved'].includes(x.review_status);
        const published = x.publishing_status === 'published';
        return <div className="card" key={x.id}>
          <div className="row"><b>{x.platform}</b><span className="badge">{x.approval_status}</span></div>
          <p className="muted"><b>Type:</b> {x.content_type} · <b>Topic:</b> {x.topic}</p>
          <textarea disabled={published || !!busy} value={editing[x.id] ?? x.body} onChange={e => setEditing({ ...editing, [x.id]: e.target.value })} rows={8} />
          <div className="review-box">
            <b>Automated Reviewer</b>
            <p className="muted"><b>Status:</b> {x.review_status}</p>
            <p style={{ whiteSpace: 'pre-wrap' }}>{x.review_notes || 'No reviewer notes.'}</p>
          </div>
          <div className="action-group">
            <button className="button" disabled={published || !!busy} onClick={() => void action(x, 'Save edit', () => editContent(x.id, editing[x.id] ?? x.body))}>Save Edit</button>
            <button className="button" disabled={!reviewerPass || published || !!busy} onClick={() => void action(x, 'Approve', () => approve(x.id))}>Approve</button>
            <button className="button secondary" disabled={published || !!busy} onClick={() => void action(x, 'Regenerate', () => regenerate(x.id))}>Regenerate</button>
            <button className="button danger" disabled={published || !!busy} onClick={() => void action(x, 'Reject', () => reject(x.id))}>Reject</button>
            {x.approval_status === 'approved' && !published && <button className="button" disabled={!!busy} onClick={() => void action(x, 'Publish', () => publish(x.id))}>Publish</button>}
          </div>
        </div>;
      })}
      {!items.length && <div className="card"><p className="muted">No generated content yet. Run the campaign agents first.</p></div>}
    </div>
  </>;
}
