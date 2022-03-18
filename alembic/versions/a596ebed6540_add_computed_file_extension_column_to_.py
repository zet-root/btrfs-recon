"""Add computed file extension column to InodeRef

Revision ID: a596ebed6540
Revises: a7ab0413b781
Create Date: 2022-03-17 02:02:01.223063-04:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a596ebed6540'
down_revision = 'a7ab0413b781'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('inode_ref', sa.Column('ext', sa.String(), sa.Computed("CASE WHEN (strpos(name, '.') = 0) THEN NULL ELSE split_part(name, '.', -1) END", persisted=True), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('inode_ref', 'ext')
    # ### end Alembic commands ###