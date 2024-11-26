"""

Revision ID: 022
9Revises:
Create Date: 2024-11-15 14:18

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0229"
down_revision = "0228"
branch_labels = None
depends_on = None


def change_to_bool():
    change_fields = [('model_settings', 'use_2d_rain'),
                     ('physical_settings', 'use_advection_2d')]
    # this does not work, dunno why
    # alter not supported -> fix in original migrations
    for table_name, column_name in change_fields:
        op.alter_column(table_name, column_name, type_=sa.Boolean)




def upgrade():
    change_to_bool()

def downgrade():
    pass
