"""reset

Revision ID: 75614f721eb7
Revises: 
Create Date: 2024-05-07 20:46:20.730378

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '75614f721eb7'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('admin',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=20), nullable=False),
    sa.Column('email', sa.String(length=120), nullable=False),
    sa.Column('password_hash', sa.String(length=128), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email'),
    sa.UniqueConstraint('username')
    )
    op.create_table('user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=20), nullable=False),
    sa.Column('email', sa.String(length=120), nullable=False),
    sa.Column('password_hash', sa.String(length=128), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email'),
    sa.UniqueConstraint('username')
    )
    op.create_table('journey',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('total_distance', sa.Float(), nullable=False),
    sa.Column('upload_time', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('stripe_customer',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('stripe_customer_id', sa.String(length=255), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], name='fk_user_id', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('stripe_customer_id')
    )
    op.create_table('filepath',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('journey_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('image_file_path', sa.String(), nullable=False),
    sa.Column('gpx_file_path', sa.String(), nullable=False),
    sa.ForeignKeyConstraint(['journey_id'], ['journey.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('location',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('journey_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('init_latitude', sa.Float(), nullable=False),
    sa.Column('init_longitude', sa.Float(), nullable=False),
    sa.Column('goal_latitude', sa.Float(), nullable=False),
    sa.Column('goal_longitude', sa.Float(), nullable=False),
    sa.Column('departure', sa.String(length=255), nullable=False),
    sa.Column('arrival', sa.String(length=255), nullable=False),
    sa.Column('upload_time', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['journey_id'], ['journey.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('stripe_subscription',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('stripe_customer_id', sa.Integer(), nullable=False),
    sa.Column('stripe_subscription_id', sa.String(length=255), nullable=False),
    sa.Column('start_date', sa.DateTime(), nullable=False),
    sa.Column('plan', sa.String(length=255), nullable=False),
    sa.Column('active', sa.Boolean(), nullable=False),
    sa.Column('renewal_date', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['stripe_customer_id'], ['stripe_customer.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('stripe_subscription_id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('stripe_subscription')
    op.drop_table('location')
    op.drop_table('filepath')
    op.drop_table('stripe_customer')
    op.drop_table('journey')
    op.drop_table('user')
    op.drop_table('admin')
    # ### end Alembic commands ###
