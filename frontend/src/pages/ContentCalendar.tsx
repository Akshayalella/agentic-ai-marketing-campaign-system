import {useEffect,useState} from 'react';
import {calendar} from '../services/api';
import {getActiveCampaignId} from '../services/campaign';

export default function ContentCalendar(){
  const id=getActiveCampaignId();
  const [items,setItems]=useState<any[]>([]);
  useEffect(()=>{if(id) calendar(id).then(setItems).catch(()=>{})},[id]);

  if(!id) return <div className="card"><h3>Select a campaign first</h3><p className="muted">Go to Campaigns and select a campaign.</p></div>;

  return <div className="card">
    <h3>Content calendar · Campaign #{id}</h3>
    <p className="muted">Scheduled content, review state and publishing state. Publishing remains blocked until human approval.</p>
    <div style={{overflowX:'auto'}}>
      <table>
        <thead><tr><th>Date</th><th>Platform</th><th>Content type</th><th>Topic</th><th>Caption / Content</th><th>Approval</th><th>Publishing</th></tr></thead>
        <tbody>{items.map(x=><tr key={x.id}>
          <td>{x.scheduled_date}</td>
          <td>{x.platform}</td>
          <td>{x.content_type}</td>
          <td>{x.topic}</td>
          <td style={{minWidth:280,whiteSpace:'pre-wrap'}}>{x.body}</td>
          <td>{x.approval_status}</td>
          <td>{x.publishing_status}</td>
        </tr>)}</tbody>
      </table>
    </div>
  </div>
}
