import csv, io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

def csv_bytes(items):
    out=io.StringIO(); writer=csv.writer(out)
    writer.writerow(["id","platform","type","topic","body","approval_status","publishing_status","date"])
    for x in items:
        writer.writerow([x.id,x.platform,x.content_type,x.topic,x.body,x.approval_status,x.publishing_status,x.scheduled_date])
    return out.getvalue().encode()

def pdf_bytes(campaign, items, strategy=None, research=None, analytics=None):
    buf=io.BytesIO(); c=canvas.Canvas(buf,pagesize=A4)
    width,height=A4; y=height-45
    def line(text,bold=False,size=9):
        nonlocal y
        if y < 55:
            c.showPage(); y=height-45
        c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
        # Keep output safe for built-in PDF font.
        safe=str(text).encode("latin-1","replace").decode("latin-1")
        c.drawString(40,y,safe[:115]); y-=14
    line("Agentic AI Marketing Campaign Report",True,18); y-=8
    for label,value in [("Product",campaign.product_name),("Objective",campaign.objective),
                        ("Budget",f"INR {campaign.budget:,.2f}"),("Duration",f"{campaign.duration_days} days"),
                        ("Platforms",campaign.platforms),("Brand tone",campaign.brand_tone)]:
        line(f"{label}: {value}")
    line("Campaign Strategy",True,13)
    if strategy:
        line(f"Theme: {strategy.get('theme','')}")
        line(f"Channels: {', '.join(strategy.get('channels',[]))}")
        line(f"KPIs: {', '.join(strategy.get('kpis',[]))}")
        line(f"Budget allocation: {strategy.get('budget_allocation',{})}")
    line("Research Sources",True,13)
    for s in (research or [])[:8]:
        line(f"- {s.get('title','Source')} [{s.get('source_type','unknown')}]")
        line(s.get('url',''))
        line(s.get('summary',''))
    line("Analytics",True,13)
    for k,v in (analytics or {}).items():
        line(f"{k}: {v}")
    line("Content Calendar & Approval Status",True,13)
    for x in items:
        line(f"{x.scheduled_date} | {x.platform} | {x.content_type} | approval={x.approval_status} | publish={x.publishing_status}")
    c.save(); return buf.getvalue()
