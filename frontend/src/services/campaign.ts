const KEY='activeCampaignId';
export function getActiveCampaignId(): number | null {
  const raw=localStorage.getItem(KEY);
  if (!raw) return null;
  const id=Number(raw);
  return Number.isFinite(id) && id>0 ? id : null;
}
export function setActiveCampaignId(id:number){localStorage.setItem(KEY,String(id));}
export function clearActiveCampaignId(){localStorage.removeItem(KEY);}
export function getCampaignDisplayNumber(data: any[], id: number | null): number | null {
  if (!id) return null;
  const index = data.findIndex(c => Number(c.id) === Number(id));
  return index >= 0 ? index + 1 : null;
}
