import { useEffect, useState } from 'react';
import { apiErrorMessage, campaigns, report } from '../services/api';
import { getActiveCampaignId, getCampaignDisplayNumber } from '../services/campaign';

const base = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export default function Reports() {
  const id = getActiveCampaignId();
  const [r, setR] = useState<any>();
  const [error, setError] = useState('');
  const [campaignList, setCampaignList] = useState<any[]>([]);

  useEffect(() => {
    if (!id) return;
    Promise.all([report(id), campaigns()]).then(([reportData, allCampaigns]) => { setR(reportData); setCampaignList(allCampaigns); }).catch(e => setError(apiErrorMessage(e)));
  }, [id]);

  if (!id) return <div className="card"><h3>Select a campaign first</h3><p className="muted">Go to Campaigns and select a campaign.</p></div>;
  return <div className="grid2">
    <div className="card">
      <h3>Campaign report · #{getCampaignDisplayNumber(campaignList, id) ?? 1}</h3>
      <p className="muted">Consolidated strategy, research, content calendar, approvals and analytics.</p>
      {error && <p className="error">{error}</p>}
      {r && <>
        <p><b>Product:</b> {r.campaign?.product_name}</p>
        <p><b>Theme:</b> {r.strategy?.theme}</p>
        <p><b>Workflow:</b> {r.workflow_status}</p>
        <p><b>Content:</b> {r.content_calendar?.length || 0} items</p>
        <p><b>Analytics:</b> {r.analytics?.observed ? 'Observed' : 'Projected'}</p>
        {r.analytics?.performance_score != null && <p><b>Performance score:</b> {r.analytics.performance_score}/100</p>}
      </>}
      <a className="button" href={`${base}/api/campaigns/${id}/export/pdf`}>Download PDF</a>
    </div>
    <div className="card"><h3>Content data</h3><p className="muted">Export generated content, approval status and publishing status as CSV.</p><a className="button" href={`${base}/api/campaigns/${id}/export/csv`}>Download CSV</a></div>
  </div>;
}
