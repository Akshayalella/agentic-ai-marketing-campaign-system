import {useEffect,useState} from 'react';
import {campaigns,runCampaign} from '../services/api';
import {setActiveCampaignId} from '../services/campaign';

export default function Campaigns(){
  const [data,setData]=useState<any[]>([]);

  const load=()=>{
    campaigns().then(setData).catch(()=>{});
  };

  useEffect(()=>{
    load();
  },[]);

  return <div className="card">
    <div className="row">
      <h3>Campaigns</h3>
      <a className="button" href="/create">New campaign</a>
    </div>

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
        {data.map(c=>
          <tr key={c.id}>
            <td>{c.product_name}</td>
            <td>{c.objective}</td>
            <td>₹{c.budget}</td>
            <td>{c.workflow_status}</td>
            <td>
              <button
                className="button secondary"
                onClick={()=>{
                  setActiveCampaignId(c.id);
                  load();
                }}
              >
                Select
              </button>

              <button
                className="button"
                onClick={()=>{
                  setActiveCampaignId(c.id);
                  runCampaign(c.id).then(load);
                }}
              >
                Run agents
              </button>
            </td>
          </tr>
        )}
      </tbody>
    </table>
  </div>;
}