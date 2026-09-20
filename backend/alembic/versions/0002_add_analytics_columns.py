"""Add projected and observed analytics JSON storage to campaigns."""
from alembic import op
import sqlalchemy as sa

revision = "0002_analytics_columns"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "campaigns",
        sa.Column("projected_analytics", sa.Text(), nullable=False, server_default="{}"),
    )
    op.add_column(
        "campaigns",
        sa.Column("observed_analytics", sa.Text(), nullable=False, server_default="{}"),
    )


def downgrade():
    op.drop_column("campaigns", "observed_analytics")
    op.drop_column("campaigns", "projected_analytics")
