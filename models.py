from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import CheckConstraint
from datetime import datetime

db = SQLAlchemy()

class Users(db.Model):
    __tablename__= 'users'

    user_id=db.Column(db.Integer, primary_key=True, autoincrement=True)
    username=db.Column(db.String, unique=True, nullable=False)
    password=db.Column(db.String, nullable=False)
    user_type=db.Column(db.String, nullable=False)
    email=db.Column(db.String, unique=True)
    name=db.Column(db.String)

    sponsors = db.relationship('Sponsors', back_populates='user', uselist=False)
    influencers = db.relationship('Influencers', back_populates='user', uselist=False)
    messages_sent = db.relationship('Messages', foreign_keys='Messages.sender_id', back_populates='sender', lazy=True)
    messages_received = db.relationship('Messages', foreign_keys='Messages.receiver_id', back_populates='receiver', lazy=True)
    flagged_users = db.relationship('Flagged_Users', back_populates='user', lazy=True)

    def __init__(self, username, password, user_type, email, name):
        self.username=username
        self.password=password
        self.user_type=user_type
        self.email=email
        self.name=name

class Sponsors(db.Model):
    __tablename__= 'sponsors'
    
    sponsor_id=db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id=db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    company_name=db.Column(db.String, nullable=False)
    industry=db.Column(db.String)
    budget=db.Column(db.Float)

    user = db.relationship('Users', back_populates='sponsors')
    campaigns = db.relationship('Campaigns', back_populates='sponsor', lazy=True)

    def __init__(self, user_id, company_name, industry, budget):
        self.user_id=user_id
        self.company_name=company_name
        self.industry=industry
        self.budget=budget
        

class Influencers(db.Model):
    __tablename__='influencers'

    influencer_id=db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id=db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    category=db.Column(db.String, nullable=False)
    niche=db.Column(db.String)
    reach=db.Column(db.Integer)
    profile_pic=db.Column(db.String)

    user = db.relationship('Users', back_populates='influencers')
    ad_requests = db.relationship('Ad_Requests', back_populates='influencer', lazy=True)

    def __init__(self, user_id, category, niche, reach, profile_pic=None):
        self.user_id=user_id
        self.category=category
        self.niche=niche
        self.reach=reach
        self.profile_pic=profile_pic

class Campaigns(db.Model):
    __tablename__='campaigns'

    campaign_id=db.Column(db.Integer, primary_key=True, autoincrement=True)
    sponsor_id=db.Column(db.Integer, db.ForeignKey('sponsors.sponsor_id'), nullable=False)
    name=db.Column(db.String, nullable=False)
    description=db.Column(db.Text)
    start_date=db.Column(db.Date)
    end_date=db.Column(db.Date)
    budget=db.Column(db.Float)
    visibility=db.Column(db.String, nullable=False)
    goals=db.Column(db.Text)
    flagged= db.Column(db.Boolean, default=False)

    sponsor = db.relationship('Sponsors', back_populates='campaigns')
    ad_requests = db.relationship('Ad_Requests', back_populates='campaign', lazy=True, overlaps="ad_requests_relation")

    __table_args__ = (
        CheckConstraint("visibility IN ('Public', 'Private')", name='check_visibility'),
    )

    def __init__(self, sponsor_id, name, description=None, start_date=None, end_date=None, budget=None, visibility='public', goals=None):
        self.sponsor_id=sponsor_id
        self.name=name
        self.description=description
        self.start_date=start_date
        self.end_date=end_date
        self.budget=budget
        self.visibility=visibility
        self.goals=goals

class Ad_Requests(db.Model):
    __tablename__='ad_requests'

    ad_request_id=db.Column(db.Integer, primary_key=True, autoincrement=True)
    campaign_id=db.Column(db.Integer, db.ForeignKey('campaigns.campaign_id'), nullable=False)
    influencer_id=db.Column(db.Integer, db.ForeignKey('influencers.influencer_id'), nullable=False)
    ad_name = db.Column(db.String(255), nullable=False)
    requirements=db.Column(db.Text)
    payment_amount=db.Column(db.Float)
    status=db.Column(db.Text, nullable=False)
    negotiation_terms=db.Column(db.Text, nullable=True)

    campaign = db.relationship('Campaigns', back_populates='ad_requests', overlaps="ad_requests_relation")
    influencer = db.relationship('Influencers', back_populates='ad_requests')

    messages = db.relationship('Messages', back_populates='ad_request', lazy=True)

    def __init__(self, campaign_id, influencer_id, ad_name, status,requirements=None, payment_amount=None, negotiation_terms=None):
        self.campaign_id=campaign_id
        self.influencer_id=influencer_id
        self.ad_name=ad_name
        self.requirements=requirements
        self.payment_amount=payment_amount
        self.status=status
        self.negotiation_terms=negotiation_terms

class Messages(db.Model):
    __tablename__='messages'

    message_id=db.Column(db.Integer, primary_key=True, autoincrement=True)
    ad_request_id=db.Column(db.Integer, db.ForeignKey('ad_requests.ad_request_id'))
    sender_id=db.Column(db.Integer, db.ForeignKey('users.user_id'))
    receiver_id=db.Column(db.Integer, db.ForeignKey('users.user_id'))
    message=db.Column(db.Text)

    sender = db.relationship('Users', foreign_keys=[sender_id], back_populates='messages_sent')
    receiver = db.relationship('Users', foreign_keys=[receiver_id], back_populates='messages_received')
    ad_request = db.relationship('Ad_Requests', back_populates='messages')


    def __init__(self, ad_request_id, sender_id, receiver_id, message):
        self.ad_request_id=ad_request_id
        self.sender_id=sender_id
        self.receiver_id=receiver_id
        self.message=message


class Flagged_Users(db.Model):
    __tablename__='flagged_users'

    flag_id=db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id=db.Column(db.Integer, db.ForeignKey('users.user_id'))
    reason=db.Column(db.Text)
    flag_date=db.Column(db.DateTime)

    user = db.relationship('Users', back_populates='flagged_users')

    def __init__(self, user_id, reason, flag_date):
        self.user_id=user_id
        self.reason=reason 
        self.flag_date=flag_date
    

class Statistics(db.Model):
    _tablename_='stats'

    stat_id= db.Column(db.Integer, primary_key=True, autoincrement=True)
    total_users= db.Column(db.Integer, nullable=False, default=0)
    active_users= db.Column(db.Integer, nullable=False, default=0)
    total_campaigns= db.Column(db.Integer, nullable=False, default=0)
    public_campaigns= db.Column(db.Integer, nullable=False, default=0)
    private_campaigns= db.Column(db.Integer, nullable=False, default=0)
    total_ad_requests= db.Column(db.Integer, nullable=False, default=0)
    pending_ad_requests= db.Column(db.Integer, nullable=False, default=0)
    accepted_ad_requests= db.Column(db.Integer, nullable=False, default=0)
    rejected_ad_requests= db.Column(db.Integer, nullable=False, default=0)
    flagged_users= db.Column(db.Integer, nullable=False, default=0)
    no_of_sponsors=db.Column(db.Integer, nullable=False, default=0)
    no_of_influencers= db.Column(db.Integer, nullable=False, default=0)

    def __init__(self, total_users, active_users, total_campaigns, public_campaigns, private_campaigns, total_ad_requests, pending_ad_requests, accepted_ad_requests, rejected_ad_requests, flagged_users, no_of_sponsors, no_of_influencers):
        self.total_users= total_users
        self.active_users= active_users
        self.total_campaigns= total_campaigns
        self.public_campaigns= public_campaigns
        self.private_campaigns= private_campaigns
        self.total_ad_requests= total_ad_requests
        self.pending_ad_requests= pending_ad_requests
        self.accepted_ad_requests= accepted_ad_requests
        self.rejected_ad_requests= rejected_ad_requests
        self.flagged_users= flagged_users
        self.no_of_sponsors= no_of_sponsors
        self.no_of_influencers= no_of_influencers


