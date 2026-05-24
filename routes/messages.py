from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models.schema import db, User, Message, Notification

messages_bp = Blueprint('messages', __name__, url_prefix='/messages')

@messages_bp.route('/')
def inbox():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    try:
        from models.schema import Job
        # Get unique pairs of (other_user_id, job_id) the current user has chatted with
        sent_to = db.session.query(Message.receiver_id, Message.job_id).filter(Message.sender_id == session['user_id'])
        received_from = db.session.query(Message.sender_id, Message.job_id).filter(Message.receiver_id == session['user_id'])
        
        pairs = sent_to.union(received_from).all()
        
        contacts = []
        for other_id, j_id in pairs:
            other_user = User.query.get(other_id)
            job = Job.query.get(j_id) if j_id else None
            if other_user:
                contacts.append({
                    'id': other_user.id,
                    'name': other_user.name,
                    'role': other_user.role,
                    'job_id': j_id,
                    'job_title': job.title if job else 'General Inquiry'
                })
        
        # If a specific user and job are selected for chat
        selected_user_id = request.args.get('user_id', type=int)
        selected_job_id = request.args.get('job_id', type=int)
        chat_messages = []
        selected_user = None
        selected_job = None
        
        if selected_user_id:
            selected_user = User.query.get(selected_user_id)
            if selected_job_id:
                selected_job = Job.query.get(selected_job_id)
            
            if selected_user:
                # Filter by both user and job
                chat_messages = Message.query.filter(
                    (((Message.sender_id == session['user_id']) & (Message.receiver_id == selected_user_id)) |
                     ((Message.sender_id == selected_user_id) & (Message.receiver_id == session['user_id']))) &
                    (Message.job_id == selected_job_id)
                ).order_by(Message.created_at.asc()).all()
                
        return render_template('messages.html', 
                               contacts=contacts, 
                               chat_messages=chat_messages, 
                               selected_user=selected_user,
                               selected_job=selected_job)
    except Exception as e:
        flash(f"Inbox error: {str(e)}", "error")
        return redirect(url_for('index'))

@messages_bp.route('/send', methods=['POST'])
def send_message():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    receiver_id = request.form.get('receiver_id', type=int)
    job_id = request.form.get('job_id', type=int)
    content = request.form.get('content')
    
    if not content:
        flash('Message cannot be empty.', 'error')
        return redirect(url_for('messages.inbox', user_id=receiver_id, job_id=job_id))
        
    try:
        new_msg = Message(sender_id=session['user_id'], receiver_id=receiver_id, job_id=job_id, content=content)
        db.session.add(new_msg)
        
        # Notify the receiver
        notif_msg = f"New message regarding {Job.query.get(job_id).title if job_id else 'job'}: {content[:50]}..."
        action_url = url_for('messages.inbox', user_id=session['user_id'], job_id=job_id)
        new_notif = Notification(user_id=receiver_id, message=notif_msg[:490], action_url=action_url)
        db.session.add(new_notif)
        
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f"Error sending message: {str(e)}", "error")
        
    return redirect(url_for('messages.inbox', user_id=receiver_id, job_id=job_id))
