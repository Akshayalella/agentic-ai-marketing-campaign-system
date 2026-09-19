import { useEffect, useState } from 'react';
import {
  content,
  approve,
  reject,
  regenerate,
  editContent,
  publish,
} from '../services/api';
import { getActiveCampaignId } from '../services/campaign';

export default function ContentStudio() {
  const id = getActiveCampaignId();

  const [items, setItems] = useState<any[]>([]);
  const [editing, setEditing] = useState<Record<number, string>>({});

  const load = () => {
    if (id) {
      content(id)
        .then(setItems)
        .catch(() => {});
    }
  };

  useEffect(() => {
    load();
  }, [id]);

  if (!id) {
    return (
      <div className="card">
        <h3>Select a campaign first</h3>
        <p className="muted">
          Go to Campaigns and select a campaign.
        </p>
      </div>
    );
  }

  return (
    <>
      <div className="hero">
        <h2>Content Studio · Campaign #{id}</h2>
        <p className="muted">
          Edit and review AI-generated content. Approval is required before
          publishing.
        </p>
      </div>

      <div className="grid2">
        {items.map((x) => (
          <div className="card" key={x.id}>
            <div className="row">
              <b>{x.platform}</b>
              <span className="badge">{x.approval_status}</span>
            </div>

            <h3>{x.topic}</h3>

            <textarea
              value={editing[x.id] ?? x.body}
              onChange={(e) =>
                setEditing({
                  ...editing,
                  [x.id]: e.target.value,
                })
              }
              rows={8}
            />

            <div
              className="row"
              style={{ marginTop: 15, flexWrap: 'wrap' }}
            >
              <button
                className="button"
                onClick={() =>
                  editContent(x.id, editing[x.id] ?? x.body).then(load)
                }
              >
                Save Edit
              </button>

              <button
                className="button"
                onClick={() => approve(x.id).then(load)}
              >
                Approve
              </button>

              <button
                className="button secondary"
                onClick={() => regenerate(x.id).then(load)}
              >
                Regenerate
              </button>

              <button
                className="button danger"
                onClick={() => reject(x.id).then(load)}
              >
                Reject
              </button>

              {x.approval_status === 'approved' && (
                <button
                  className="button"
                  onClick={() => publish(x.id).then(load)}
                >
                  Publish
                </button>
              )}
            </div>

            <p className="muted">{x.review_notes}</p>
          </div>
        ))}
      </div>
    </>
  );
}