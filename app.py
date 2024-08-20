import os
import re
from sqlite3 import IntegrityError
from flask import Flask, request, render_template, redirect, url_for, session, flash, current_app, jsonify
from models import db, Users, Sponsors, Influencers, Campaigns, Ad_Requests, Flagged_Users, Messages, Statistics
from werkzeug.utils import secure_filename
current_dir=os.path.abspath(os.path.dirname(__file__))
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'MyProject'
app.config['SQLALCHEMY_DATABASE_URI']="sqlite:///"+ os.path.join(current_dir, "users.sqlite3")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static/uploads')

db.init_app(app)

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

@app.route('/')
def main():
    return render_template('login.html')


#LOGIN
@app.route('/login', methods=['GET', 'POST'])
def login():
    error= None
    if request.method == 'POST':
        username=request.form['username']
        password=request.form['password']
        user=Users.query.filter_by(username=username, password=password).first()
        if user:
            session['user_id']=user.user_id
            session['user_type']=user.user_type
            if user.user_type == 'Admin':
                return redirect(url_for('admin_info'))
            elif user.user_type == 'Sponsor':
                return redirect(url_for('sponsor_profile'))
            elif user.user_type == 'Influencer':
                return redirect(url_for('influencers_dashboard'))
        else:
            error = "Invalid credentials"
    return render_template('login.html', error=error)



#REGISTER
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user_type = request.form.get('user_type')
        email = request.form.get('email')
        name = request.form.get('name')
        company_name = request.form.get('company_name')
        industry = request.form.get('industry')
        budget = request.form.get('budget')
        category = request.form.get('category')
        niche = request.form.get('niche')
        reach = request.form.get('reach')
        
        # Validate user fields
        if not re.match(r'^[a-zA-Z0-9]{5,}$', username):
            flash('Username must be at least 5 alphanumeric characters', 'error')
            return render_template('register.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters long', 'error')
            return render_template('register.html')

        if not re.match(r'^\S+@\S+\.\S+$', email):
            flash('Please enter a valid email', 'error')
            return render_template('register.html')

        if user_type == 'Sponsor':
            if not company_name or not industry or not budget:
                flash('Please fill in all Sponsor fields correctly', 'error')
                return render_template('register.html')

            try:
                budget = float(budget)
            except ValueError:
                flash('Budget must be a number', 'error')
                return render_template('register.html')

        elif user_type == 'Influencer':
            if not category or not niche or not reach:
                flash('Please fill in all Influencer fields correctly', 'error')
                return render_template('register.html')

            try:
                reach = int(reach)
            except ValueError:
                flash('Reach must be a number', 'error')
                return render_template('register.html')

        try:
            new_user = Users(username=username, password=password, user_type=user_type, email=email, name=name)
            db.session.add(new_user)
            db.session.flush()
            print(f"New user created with ID: {new_user.user_id}")

            if user_type == 'Sponsor':
                sponsor = Sponsors(user_id=new_user.user_id, company_name=company_name, industry=industry, budget=budget)
                db.session.add(sponsor)
                print(f"Sponsor created with user ID: {new_user.user_id}")

            elif user_type == 'Influencer':
                influencer = Influencers(user_id=new_user.user_id, category=category, niche=niche, reach=reach)
                db.session.add(influencer)
                print(f"Influencer created with user ID: {new_user.user_id}")

            db.session.commit()
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()  
            print(f"Error occurred: {e}")
            return render_template('register.html')

    return render_template('register.html')

#LOGOUT 
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))




#ADMIN
@app.route('/admin/info')
def admin_info():
    campaigns = Campaigns.query.all()
    flagged_users= db.session.query(Flagged_Users, Users).join(Users).all()
    return render_template('admin_info.html', campaigns=campaigns, flagged_users=flagged_users)

@app.route('/admin/stats')
def admin_stats():
    stats= Statistics.query.first()
    return render_template('admin_stats.html', stats=stats)

@app.route('/api/statistics')
def api_statistics():
    update_statistics()
    stats= Statistics.query.first()
    stats_data={
        "total_users": stats.total_users,
        "active_users": stats.active_users,
        "no_of_sponsors": stats.no_of_sponsors,
        "no_of_influencers": stats.no_of_influencers,
        "total_campaigns": stats.total_campaigns,
        "total_ad_requests": stats.total_ad_requests,
        "flagged_users": stats.flagged_users,
        "public_campaigns": stats.public_campaigns,
        "private_campaigns": stats.private_campaigns,
        "pending_ad_requests": stats.pending_ad_requests,
        "accepted_ad_requests": stats.accepted_ad_requests,
        "rejected_ad_requests": stats.rejected_ad_requests
    }
    return jsonify(stats_data)


@app.route('/admin/find')
def admin_find():
    return render_template('admin_find.html')


@app.route('/search_campaigns', methods=['GET'])
def search_campaigns():
    campaign_name = request.args.get('campaign_name', '')
    campaigns = []
    if campaign_name:
        campaigns = Campaigns.query.filter(Campaigns.name.ilike(f'%{campaign_name}%')).all()
    if not campaigns:
        flash('No campaigns found matching your search criteria.', 'info')
    return render_template('admin_find.html', campaigns=campaigns)

@app.route('/search_users', methods=['GET'])
def search_users():
    username = request.args.get('username', '')
    user_type = request.args.get('user_type', '')
    users = []
    if username or user_type:
        query=Users.query
        if username:
            query=query.filter(Users.username.ilike(f'%{username}%'))
        if user_type:
            query=query.filter(Users.user_type == user_type)
        users=query.all()
    if not users:
        flash('No users found matching your search criteria.', 'info')

    return render_template('admin_find.html', users=users)

@app.route('/flag_campaign', methods=['POST'])
def flag_campaign():
    campaign_id=request.form.get('campaign_id')
    campaign=Campaigns.query.get(campaign_id)
    if campaign:
        campaign.flagged = True
        db.session.commit()
        flash(f'Campaign with ID {campaign_id} has been flagged.', 'success')
    else:
        flash(f'Campaign with ID {campaign_id} not found.', 'error')
    return redirect(url_for('admin_find'))

@app.route('/unflag_campaign', methods=['POST'])
def unflag_campaign():
    campaign_id= request.form.get('campaign_id')
    campaign=Campaigns.query.get(campaign_id)
    if campaign:
        campaign.flagged=False
        db.session.commit()
        flash(f'Campaign with ID {campaign_id} has been unflagged.', 'success')
    else:
        flash(f'Campaign with ID {campaign_id} not found.', 'error')

    return redirect(url_for('admin_info'))


@app.route('/flag_user', methods=['POST'])
def flag_user():
    user_id = request.form.get('user_id')
    reason = request.form.get('reason', 'No reason provided')
    user = Users.query.get(user_id)
    if user:
        flag_date= datetime.now()
        flagged_user=Flagged_Users(user_id=user_id, reason=reason, flag_date=flag_date)
        db.session.add(flagged_user)
        db.session.commit()
        flash(f'User with ID {user_id} has been flagged.', 'success')
    else:
        flash(f'User with ID {user_id} not found.', 'error')
    return redirect(url_for('admin_find'))

@app.route('/unflag_user', methods=['POST'])
def unflag_user():
    user_id= request.form.get('user_id')
    flagged_user= Flagged_Users.query.filter_by(user_id=user_id).first()
    if flagged_user:
        db.session.delete(flagged_user)
        db.session.commit()
        flash(f'User with ID {user_id} has been unflagged.', 'success')
    else:
        flash(f'User with ID {user_id} not found.', 'error')
    return redirect(url_for('admin_info'))

    



#SPONSORS
@app.route('/sponsor/profile')
def sponsor_profile():
    sponsor_id=session.get('user_id')
    sponsor=Sponsors.query.filter_by(user_id=sponsor_id).first()
    active_campaigns=Campaigns.query.filter_by(sponsor_id=sponsor.sponsor_id).all()
    new_requests = Ad_Requests.query.join(Campaigns).filter(Campaigns.sponsor_id == sponsor.sponsor_id, Ad_Requests.status == 'pending').all()
    return render_template('sponsor_profile.html', sponsor=sponsor, active_campaigns=active_campaigns, new_requests=new_requests)

@app.route('/sponsor/campaigns')
def sponsor_campaigns():
    sponsor_id=session.get('user_id')
    sponsor=Sponsors.query.filter_by(user_id=sponsor_id).first()
    campaign_ad_requests={}
    campaigns=Campaigns.query.filter_by(sponsor_id=sponsor.sponsor_id).all()
    for campaign in campaigns:
        ad_requests= Ad_Requests.query.filter_by(campaign_id=campaign.campaign_id).all()
        campaign_ad_requests[campaign.campaign_id]= ad_requests
    return render_template('sponsor_campaigns.html', campaigns=campaigns, campaign_ad_requests= campaign_ad_requests)

@app.route('/sponsor/campaigns/add', methods=['GET', 'POST'])
def add_campaign():
    if request.method == 'POST':
        sponsor_id = session.get('user_id')
        sponsor = Sponsors.query.filter_by(user_id=sponsor_id).first()
        name = request.form['name']
        description = request.form['description']
        start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date()
        budget = float(request.form['budget'])
        visibility = request.form['visibility']
        goals = request.form['goals']

        new_campaign = Campaigns(
            sponsor_id=sponsor.sponsor_id,
            name=name,
            description=description,
            start_date=start_date,
            end_date=end_date,
            budget=budget,
            visibility=visibility,
            goals=goals
        )
        db.session.add(new_campaign)
        db.session.commit()
        return redirect(url_for('sponsor_campaigns'))
    
    return render_template('add_campaign.html')

@app.route('/sponsor/campaigns/<int:campaign_id>/add_request', methods=['GET', 'POST'])
def add_ad_request(campaign_id):
    if request.method == 'POST':
        print(request.form)
        
        try:
            influencer_id = request.form['influencer_id']
            ad_name = request.form['ad_name']
            requirements = request.form['requirements']
            payment_amount = float(request.form['payment_amount'])
            status = request.form['status']
            negotiation_terms= request.form['negotiation_terms']
            message_content= request.form['message']
            
            new_ad_request = Ad_Requests(
                campaign_id=campaign_id,
                influencer_id=influencer_id,
                ad_name=ad_name,
                requirements=requirements,
                payment_amount=payment_amount,
                status=status,
                negotiation_terms=negotiation_terms
            )
            db.session.add(new_ad_request)
            db.session.commit()

            new_message=Messages(
                ad_request_id=new_ad_request.ad_request_id,
                sender_id=session.get('user_id'),
                receiver_id=influencer_id,
                message=message_content
            )
            db.session.add(new_message)
            db.session.commit()

            flash('Ad request created successfully.', 'success')
            return redirect(url_for('sponsor_campaigns'))
        
        except KeyError as e:
            print(f"Missing form field: {e}")
            return "Missing form field", 400
        except ValueError as e:
            print(f"Invalid value: {e}")
            return "Invalid value", 400
    
    campaign = Campaigns.query.get(campaign_id)
    influencers = Influencers.query.all()
    return render_template('add_ad_request.html', campaign=campaign, influencers=influencers)


@app.route('/campaign/update/<int:campaign_id>', methods=['GET', 'POST'])
def update_campaign(campaign_id):

    campaign = Campaigns.query.filter_by(campaign_id=campaign_id).first()
    if not campaign:
        flash('Campaign not found!', 'error')
        return redirect(url_for('sponsor_campaigns'))

    if request.method == 'POST':
        try:
            print("Form data received:")
            print("Name:", request.form['name'])
            print("Description:", request.form['description'])
            print("Start Date:", request.form['start_date'])
            print("End Date:", request.form['end_date'])
            print("Budget:", request.form['budget'])
            print("Visibility:", request.form['visibility'])
            print("Goals:", request.form['goals'])

            campaign.name=request.form['name']
            campaign.description= request.form['description']
            campaign.start_date=datetime.strptime(request.form['start_date'], '%Y-%m-%d')
            campaign.end_date=datetime.strptime(request.form['end_date'], '%Y-%m-%d')
            campaign.budget=float(request.form['budget'])
            campaign.visibility=request.form['visibility']
            campaign.goals=request.form['goals']

            try:
                db.session.commit()
                print("Changes committed to the database")
            except Exception as e:
                db.session.rollback()
                print(f"Error committing changes to the database: {str(e)}")
            finally:
                db.session.close()

        except ValueError as ve:
            db.session.rollback()
            flash(f'Value error: {str(ve)}', 'error')
        except IntegrityError as ie:
            db.session.rollback()
            flash(f'Integrity error: {str(ie.orig)}', 'error')
        except Exception as e:
            db.session.rollback()
            flash(f'An unexpected error occurred: {str(e)}', 'error')
            
        return redirect(url_for('sponsor_campaigns'))
    return render_template('update_campaign.html', campaign=campaign)


@app.route('/campaign/delete/<int:campaign_id>', methods=['POST', 'GET'])
def delete_campaign(campaign_id):
    campaign = Campaigns.query.get_or_404(campaign_id)
    db.session.delete(campaign)
    db.session.commit()
    flash('Campaign deleted successfully!')
    return redirect(url_for('sponsor_campaigns'))


@app.route('/sponsor_dashboard/update_ad_request/<int:ad_request_id>', methods=['GET','POST'])
def update_ad_request(ad_request_id):
    ad_request = Ad_Requests.query.get_or_404(ad_request_id)
    if request.method == 'POST':

        ad_request.requirements = request.form['requirements']
        ad_request.payment_amount = float(request.form['payment_amount'])
        ad_request.status = request.form['status']
   
        db.session.commit()
        flash('Ad request updated successfully!')
        return redirect(url_for('sponsor_campaigns'))
    return render_template('update_ad_request.html', ad_request=ad_request)

@app.route('/ad_request/delete/<int:ad_request_id>', methods=['POST', 'GET'])
def delete_ad_request(ad_request_id):
    ad_request = Ad_Requests.query.get_or_404(ad_request_id)
    db.session.delete(ad_request)
    db.session.commit()
    flash('Ad request deleted successfully!')
    return redirect(url_for('sponsor_campaigns'))

@app.route('/search_influencers', methods=['GET', 'POST'])
def search_influencers():
    influencers = []
    if request.method == 'POST':
        niche = request.form.get('niche')
        reach = request.form.get('reach')
        category = request.form.get('category')

        query = db.session.query(Influencers, Users).join(Users, Users.user_id == Influencers.user_id)

        if niche:
            query = query.filter(Influencers.niche.ilike(f"%{niche}%"))
        if reach:
            query = query.filter(Influencers.reach >= int(reach))
        if category:
            query = query.filter(Influencers.category.ilike(f"%{category}%"))
        
        influencers = query.all()
    
    return render_template('search_influencers.html', influencers=influencers)

@app.route('/update_ad_request_status/<int:request_id>', methods=['POST'])
def update_ad_request_status(request_id):
    new_status= request.form.get('status')
    ad_request= Ad_Requests.query.get(request_id)

    if ad_request:
        ad_request.status= new_status
        db.session.commit()
        flash(f'Ad request {request_id} status updated to {new_status}.', 'success')
    else:
        flash(f'Ad request {request_id} not found.', 'error')
    
    return redirect(url_for('sponsor_profile'))





#INFLUENCERS
@app.route('/influencers/dashboard')
def influencers_dashboard():
    if 'user_id' in session and session['user_type']=='Influencer':
        return redirect(url_for('influencer_profile'))
    return redirect(url_for('login'))

@app.route('/influencers/profile')
def influencer_profile():
    influencer_id=session.get('user_id')
    influencer=Influencers.query.filter_by(user_id=influencer_id).first_or_404()
    user= Users.query.filter_by(user_id=influencer_id).first_or_404()
    active_campaigns = Campaigns.query.join(Ad_Requests).filter(
        Ad_Requests.influencer_id == influencer.user.user_id,
        Ad_Requests.status == 'Accepted'
    ).all()
    new_requests = Ad_Requests.query.filter_by(influencer_id=influencer.user.user_id).filter(
        Ad_Requests.status == "Pending"
    ).all()
    return render_template('influencer_profile.html', influencer=influencer, active_campaigns=active_campaigns, new_requests=new_requests, user=user)


@app.route('/influencers/edit_profile', methods=['POST'])
def edit_profile():
    influencer_id= session.get('user_id')
    user= Users.query.filter_by(user_id= influencer_id).first_or_404()
    influencer= Influencers.query.filter_by(user_id= influencer_id).first_or_404()

    user.name=request.form['name']
    user.username= request.form['username']
    user.email= request.form['email']
    influencer.category=request.form['category']
    influencer.niche=request.form['niche']
    influencer.reach=request.form['reach']

    db.session.commit()
    return redirect(url_for('influencer_profile'))


@app.route('/influencer/find', methods=['GET'])
def influencer_find():
    campaign_name=request.args.get('campaign_name')
    budget= request.args.get('budget')

    query= Campaigns.query

    if campaign_name or budget:
        if campaign_name:
            query= query.filter(Campaigns.name.ilike(f"%{campaign_name}%"))
    
        if budget:
            query= query.filter(Campaigns.budget <= float(budget))
        
        influencer_id= session.get('user_id')
        campaigns= query.filter(~Campaigns.ad_requests.any(influencer_id=influencer_id)).all()
    else:
        campaigns= []

    return render_template('influencer_find.html', campaigns=campaigns)

@app.route('/update_profile_pic', methods=['POST'])
def update_profile_pic():
    if 'user_id' not in session:
        flash('Please log in to update your profile picture', 'error')
        return redirect(url_for('login'))

    influencer_id = session.get('user_id')
    influencer = Influencers.query.filter_by(user_id=influencer_id).first()

    if 'profile_pic' not in request.files:
        flash('No file part', 'error')
        return redirect(url_for('influencer_profile'))

    file = request.files['profile_pic']
    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(url_for('influencer_profile'))

    if file:
        filename = secure_filename(file.filename)
        file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
        influencer.profile_pic = filename
        db.session.commit()
        flash('Profile picture updated successfully!', 'success')
        return redirect(url_for('influencer_profile'))
    

@app.route('/influencers/apply/<int:campaign_id>', methods=['GET'])
def apply_for_campaign_form(campaign_id):
    campaign = Campaigns.query.get(campaign_id)

    if not campaign:
        flash('Campaign not found.', 'error')
        return redirect(url_for('influencer_find'))
    return render_template('apply_for_campaign.html', campaign=campaign)


@app.route('/influencer/apply/<int:campaign_id>', methods=['POST'])
def apply_for_campaign(campaign_id):
    influencer_id = session.get('user_id')
    campaign = Campaigns.query.get(campaign_id)

    if not campaign:
        flash('Campaign not found.', 'error')
        return redirect(url_for('influencer_find'))
    ad_name= request.form.get('ad_name')
    requirements= request.form.get('requirements')
    negotiation_terms= request.form.get('negotiation_terms')
    payment_amount= request.form.get('payment_amount')

    if not ad_name or not requirements or not payment_amount:
        flash('Please fill out all fields.', 'error')
        return redirect(url_for('apply_for_campaign_form', campaign_id=campaign_id))
    
    ad_request= Ad_Requests(
        campaign_id=campaign_id,
        influencer_id=influencer_id,
        ad_name=ad_name,
        requirements=requirements,
        negotiation_terms= negotiation_terms,
        payment_amount=float(payment_amount),
        status='pending'
    )

    db.session.add(ad_request)
    db.session.commit()

    flash('Application submitted successfully.', 'success')
    return redirect(url_for('influencer_find'))

    
@app.route('/respond_to_ad_request/<int:ad_request_id>', methods=['POST'])
def respond_to_ad_request(ad_request_id):
    status = request.form.get('status')

    ad_request = Ad_Requests.query.get_or_404(ad_request_id)
    ad_request.status = status
    db.session.commit()

    return redirect(url_for('influencer_profile'))


def update_statistics():
    total_users=Users.query.count()
    active_users= total_users
    no_of_sponsors= Sponsors.query.count()
    no_of_influencers= Influencers.query.count()
    total_campaigns=Campaigns.query.count()
    public_campaigns=Campaigns.query.filter_by(visibility='public').count()
    private_campaigns=Campaigns.query.filter_by(visibility='private').count()
    total_ad_requests=Ad_Requests.query.count()
    pending_ad_requests= Ad_Requests.query.filter_by(status='Pending').count()
    accepted_ad_requests=Ad_Requests.query.filter_by(status='Accepted').count()
    rejected_ad_requests= Ad_Requests.query.filter_by(status='Rejected').count()
    flagged_users=Flagged_Users.query.count()

    stats= Statistics.query.first()
    if not stats:
        stats= Statistics(
            total_users=total_users,
            active_users=active_users,
            no_of_sponsors=no_of_sponsors,
            no_of_influencers=no_of_influencers,
            total_campaigns=total_campaigns,
            public_campaigns=public_campaigns,
            private_campaigns=private_campaigns,
            total_ad_requests=total_ad_requests,
            pending_ad_requests=pending_ad_requests,
            accepted_ad_requests=accepted_ad_requests,
            rejected_ad_requests=rejected_ad_requests,
            flagged_users=flagged_users
        )
        db.session.add(stats)

    else:
        stats.total_users= total_users
        stats.active_users= active_users
        stats.total_campaigns= total_campaigns
        stats.public_campaigns= public_campaigns
        stats.private_campaigns= private_campaigns
        stats.total_ad_requests= total_ad_requests
        stats.pending_ad_requests= pending_ad_requests
        stats.accepted_ad_requests= accepted_ad_requests
        stats.rejected_ad_requests= rejected_ad_requests
        stats.flagged_users= flagged_users
        stats.no_of_sponsors= no_of_sponsors
        stats.no_of_influencers= no_of_influencers

    db.session.commit()


if __name__=='__main__':
    app.run(debug=True)
