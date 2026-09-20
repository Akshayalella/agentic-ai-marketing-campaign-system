import {useState} from 'react';
import {analytics,analyticsUpload} from '../services/api';
import {getActiveCampaignId} from '../services/campaign';

export default function Analytics(){
  const id=getActiveCampaignId();
  const [r,setR]=useState<any>();
  const [targets,setTargets]=useState({engagement_rate:'',ctr:'',conversion_rate:'',cost_per_lead:''});

  if(!id) return <div className="card"><h3>Select a campaign first</h3><p className="muted">Go to Campaigns and select a campaign.</p></div>;

  const run=()=>{
    analytics(id,{
      impressions:10000,engagements:800,clicks:500,conversions:75,
      spending:12000,leads:60,observed:false,
      targets:Object.fromEntries(Object.entries(targets).filter(([,v])=>v!=='').map(([k,v])=>[k,Number(v)]))
    }).then(setR).catch(()=>{});
  };

  const upload=(e:any)=>{
    const f=e.target.files?.[0];
    if(f) analyticsUpload(id,f).then(setR).catch(()=>{});
  };

  return <div className="card">
    <h3>Campaign analytics · #{id}</h3>
    <p className="muted">Projected metrics are labelled until observed campaign data is uploaded. Optional targets enable target comparison.</p>

    <div className="grid2">
      {[
        ['engagement_rate','Engagement target (%)'],
        ['ctr','CTR target (%)'],
        ['conversion_rate','Conversion target (%)'],
        ['cost_per_lead','CPL target (₹)']
      ].map(([k,l])=><div key={k}>
        <label>{l}</label>
        <input type="number" min="0" value={(targets as any)[k]} onChange={e=>setTargets({...targets,[k]:e.target.value})}/>
      </div>)}
    </div>

    <div className="row" style={{marginTop:15}}>
      <button className="button" onClick={run}>Calculate projected KPIs</button>
      <label className="button secondary">Upload observed CSV<input type="file" accept=".csv" hidden onChange={upload}/></label>
    </div>

    {r&&<>
      <div className="grid" style={{marginTop:18}}>
        {[
          ['Data type',r.observed?'Observed':'Projected'],
          ['Engagement rate',r.engagement_rate+'%'],
          ['CTR',r.ctr+'%'],
          ['Conversion rate',r.conversion_rate+'%'],
          ['Cost per lead','₹'+r.cost_per_lead],
          ['Spending','₹'+r.spending]
        ].map(([a,b])=><div className="card" key={a}><div className="muted">{a}</div><div className="big">{b}</div></div>)}
      </div>

      {r.target_comparison&&<div className="card" style={{marginTop:18}}>
        <h4>Target comparison</h4>
        {Object.entries(r.target_comparison).map(([k,v]:any)=><p key={k}>{k}: {v.actual} vs {v.target} — <b>{v.status}</b></p>)}
      </div>}

      {r.improvement_suggestions&&<div className="card" style={{marginTop:18}}>
        <h4>Improvement suggestions</h4>
        <ul>{r.improvement_suggestions.map((s:string,i:number)=><li key={i}>{s}</li>)}</ul>
      </div>}
    </>}
  </div>
}
