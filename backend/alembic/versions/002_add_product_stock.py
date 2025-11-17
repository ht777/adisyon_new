"""Add in_stock field to products table

Revision ID: 002_add_product_stock
Revises: 001_initial
Create Date: 2025-01-17

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002_add_product_stock'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade():
    # Add in_stock column to products table
    op.add_column('products', sa.Column('in_stock', sa.Boolean(), nullable=True, default=True))
    
    # Update existing records to have in_stock = True
    op.execute("UPDATE products SET in_stock = true WHERE in_stock IS NULL")
    
    # Make the column non-nullable
    op.alter_column('products', 'in_stock', nullable=False)


def downgrade():
    # Remove in_stock column from products table
    op.drop_column('products', 'in_stock')