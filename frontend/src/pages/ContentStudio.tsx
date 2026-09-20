import {useEffect,useState} from 'react';
import {content,approve,reject,regenerate,editContent,publish} from '../services/api';
import {getActiveCampaignId} from '../services/campaign';

export default function ContentStudio(){
  const id=getActiveCampaignId();
  const [items,setItems]=useState<any[]>([]);
  const [editing,setEditing]=useState<Record<number,string>>({});

  const load=()=>{
    if(id){
      content(id).then(setItems).catch(()=>{});
    }
  };

  useEffect(()=>{
    load();
  },[id]);

  if(!id) return <div className="card">
    <h3>Select a campaign first</h3>
    <p className="muted">Go to Campaigns and select a campaign.</p>
  </div>;

  return <>
    <div className="hero">
      <h2>Content Studio · Campaign #{id}</h2>
      <p className="muted">
        Edit and review AI-generated content. Automated review must pass and human approval is required before publishing.
      </p>
    </div>

    <div className="grid2">
      {items.map(x=>
        <div className="card" key={x.id}>
          <div className="row">
            <b>{x.platform}</b>
            <span className="badge">{x.approval_status}</span>
          </div>

          <p className="muted">
            <b>Type:</b> {x.content_type} · <b>Topic:</b> {x.topic}
          </p>

          <textarea
            value={editing[x.id]??x.body}
            onChange={e=>setEditing({...editing,[x.id]:e.target.value})}
            rows={8}
          />

          <div
            style={{
              marginTop:15,
              padding:12,
              border:'1px solid rgba(255,255,255,.12)',
              borderRadius:10
            }}
          >
            <b>Automated Reviewer</b>

            <p className="muted" style={{margin:'6px 0 0'}}>
              Status: <strong>{x.review_status}</strong>
            </p>

            <p style={{margin:'6px 0 0',whiteSpace:'pre-wrap'}}>
              {x.review_notes || 'No reviewer notes.'}
            </p>
          </div>

          <div
            className="row"
            style={{marginTop:15,flexWrap:'wrap'}}
          >
            <button
              className="button"
              onClick={()=>
                editContent(x.id,editing[x.id]??x.body).then(load)
              }
            >
              Save Edit
            </button>

            <button
              className="button"
              onClick={()=>approve(x.id).then(load)}
              disabled={!['approved_for_human_review','passed','approved'].includes(x.review_status)}
            >
              Approve
            </button>

            <button
              className="button secondary"
              onClick={()=>regenerate(x.id).then(load)}
            >
              Regenerate
            </button>

            <button
              className="button danger"
              onClick={()=>reject(x.id).then(load)}
            >
              Reject
            </button>

            {x.approval_status==='approved'&&
              <button
                className="button"
                onClick={()=>publish(x.id).then(load)}
              >
                Publish
              </button>
            }
          </div>
        </div>
      )}
    </div>
  </>;
}