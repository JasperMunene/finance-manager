"""Remove budget column to Category model

Revision ID: 6971390d6219
Revises: dbbffcabf3ff
Create Date: 2024-12-17 15:40:20.830905

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6971390d6219'
down_revision: Union[str, None] = 'dbbffcabf3ff'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('categories', 'budget')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('categories', sa.Column('budget', sa.FLOAT(), nullable=True))
    # ### end Alembic commands ###
