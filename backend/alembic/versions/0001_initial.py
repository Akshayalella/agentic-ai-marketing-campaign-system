"""Initial marketing campaign schema."""
from alembic import op
import sqlalchemy as sa

revision="0001_initial"
down_revision=None
branch_labels=None
depends_on=None

def upgrade():
    op.create_table("campaigns",
        sa.Column("id",sa.Integer,primary_key=True),
        sa.Column("product_name",sa.String(200),nullable=False),
        sa.Column("description",sa.Text,default=""),
        sa.Column("target_audience",sa.Text,default=""),
        sa.Column("objective",sa.String(300),default=""),
        sa.Column("budget",sa.Float,default=0),
        sa.Column("duration_days",sa.Integer,default=30),
        sa.Column("platforms",sa.String(500),default="LinkedIn,Email,Instagram"),
        sa.Column("brand_tone",sa.String(100),default="Professional"),
        sa.Column("brand_guidelines",sa.Text,default=""),
        sa.Column("status",sa.String(50),default="draft"),
        sa.Column("workflow_status",sa.String(80),default="not_started"),
        sa.Column("created_at",sa.DateTime,default=sa.func.now()))
    op.create_table("content_items",
        sa.Column("id",sa.Integer,primary_key=True),
        sa.Column("campaign_id",sa.Integer,sa.ForeignKey("campaigns.id"),nullable=False),
        sa.Column("platform",sa.String(50),nullable=False),
        sa.Column("content_type",sa.String(80),default="post"),
        sa.Column("topic",sa.String(300),default=""),
        sa.Column("body",sa.Text,default=""),
        sa.Column("approval_status",sa.String(40),default="pending"),
        sa.Column("publishing_status",sa.String(40),default="not_published"),
        sa.Column("review_status",sa.String(40),default="pending"),
        sa.Column("review_notes",sa.Text,default=""),
        sa.Column("scheduled_date",sa.String(20),default=""),
        sa.Column("created_at",sa.DateTime,default=sa.func.now()))
    op.create_table("approval_steps",
        sa.Column("id",sa.Integer,primary_key=True),
        sa.Column("content_id",sa.Integer,sa.ForeignKey("content_items.id"),nullable=False),
        sa.Column("status",sa.String(40),default="pending"),
        sa.Column("comment",sa.Text,default=""),
        sa.Column("updated_at",sa.DateTime,default=sa.func.now()))
    op.create_table("agent_runs",
        sa.Column("id",sa.Integer,primary_key=True),
        sa.Column("campaign_id",sa.Integer,sa.ForeignKey("campaigns.id"),nullable=False),
        sa.Column("agent_name",sa.String(120),nullable=False),
        sa.Column("status",sa.String(40),default="completed"),
        sa.Column("output",sa.Text,default=""),
        sa.Column("created_at",sa.DateTime,default=sa.func.now()))

def downgrade():
    op.drop_table("agent_runs")
    op.drop_table("approval_steps")
    op.drop_table("content_items")
    op.drop_table("campaigns")
