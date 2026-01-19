from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import datetime, date

from . import events_bp
from ..extensions import db
from ..models import Event, EventParticipant, Activity, Enrollment


def _time_to_minutes(t: str | None):
    """Convert time (HH:MM) to minutes since 00:00"""
    if not t:
        return None
    try:
        hh, mm = t.strip().split(":")
        return int(hh) * 60 + int(mm)
    except Exception:
        return None


def _times_overlap(start1, end1, start2, end2):
    """Check if two time ranges overlap"""
    s1 = _time_to_minutes(start1)
    e1 = _time_to_minutes(end1)
    s2 = _time_to_minutes(start2)
    e2 = _time_to_minutes(end2)
    
    if any(x is None for x in [s1, e1, s2, e2]):
        return False
    
    # Overlap if: start1 < end2 AND start2 < end1
    return s1 < e2 and s2 < e1


def check_schedule_conflicts(user, day, start_time, end_time):
    """Check for scheduling conflicts with courses, activities, and events"""
    conflicts = []
    
    # Check courses (enrolled students only)
    if hasattr(user, 'student') and user.student:
        enrollments = Enrollment.query.filter_by(
            student_id=user.student.id, 
            status='enrolled'
        ).all()
        
        for e in enrollments:
            c = e.course
            if c.day_of_week == day and _times_overlap(start_time, end_time, c.start_time, c.end_time):
                conflicts.append({
                    'type': 'Cours',
                    'title': c.name,
                    'time': f"{c.start_time} - {c.end_time}"
                })
    
    # Check personal activities
    activities = Activity.query.filter_by(user_id=user.id).all()
    for a in activities:
        if a.day_of_week == day and _times_overlap(start_time, end_time, a.start_time, a.end_time):
            conflicts.append({
                'type': 'Activité',
                'title': a.title,
                'time': f"{a.start_time} - {a.end_time}"
            })
    
    # Check other joined events
    participations = EventParticipant.query.filter_by(user_id=user.id).all()
    for p in participations:
        ev = p.event
        if ev.day_of_week == day and _times_overlap(start_time, end_time, ev.start_time, ev.end_time):
            conflicts.append({
                'type': 'Événement',
                'title': ev.title,
                'time': f"{ev.start_time} - {ev.end_time}"
            })
    
    return conflicts


@events_bp.route('/')
def list_events():
    """List all public events"""
    category_filter = request.args.get('category', '').strip()
    sort = request.args.get('sort', 'date').strip()
    
    query = Event.query.filter_by(is_public=True)
    
    # Filter by category
    if category_filter:
        query = query.filter_by(category=category_filter)
    
    # Sort
    if sort == 'popularity':
        # This is simplified - in production would use a subquery
        events = query.all()
        events.sort(key=lambda x: x.participant_count, reverse=True)
    elif sort == 'recent':
        events = query.order_by(Event.created_at.desc()).all()
    else:  # date
        events = query.order_by(Event.day_of_week, Event.start_time).all()
    
    categories = [
        {'value': 'study', 'label': '📚 Révisions / Étude'},
        {'value': 'sport', 'label': '⚽ Sport'},
        {'value': 'social', 'label': '🎉 Soirée / Social'},
        {'value': 'gaming', 'label': '🎮 Gaming'},
        {'value': 'food', 'label': '🍕 Restaurant / Café'},
        {'value': 'creative', 'label': '🎨 Créatif'},
        {'value': 'other', 'label': '💼 Autre'}
    ]
    
    return render_template(
        'events/list.html',
        events=events,
        categories=categories,
        current_category=category_filter,
        current_sort=sort
    )


@events_bp.route('/new')
@login_required
def new_event():
    """Show event creation form"""
    categories = [
        {'value': 'study', 'label': '📚 Révisions / Étude'},
        {'value': 'sport', 'label': '⚽ Sport'},
        {'value': 'social', 'label': '🎉 Soirée / Social'},
        {'value': 'gaming', 'label': '🎮 Gaming'},
        {'value': 'food', 'label': '🍕 Restaurant / Café'},
        {'value': 'creative', 'label': '🎨 Créatif'},
        {'value': 'other', 'label': '💼 Autre'}
    ]
    return render_template('events/create.html', categories=categories)


@events_bp.route('/create', methods=['POST'])
@login_required
def create_event():
    """Create a new event"""
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    category = request.form.get('category', 'other')
    day_of_week = request.form.get('day_of_week', '').strip()
    start_time = request.form.get('start_time', '').strip()
    end_time = request.form.get('end_time', '').strip()
    location = request.form.get('location', '').strip()
    max_participants = request.form.get('max_participants', type=int)
    
    if not all([title, day_of_week, start_time, end_time]):
        flash('Titre, jour et horaires sont requis', 'error')
        return redirect(url_for('events.new_event'))
    
    try:
        event = Event(
            creator_id=current_user.id,
            title=title,
            description=description if description else None,
            category=category,
            day_of_week=day_of_week,
            start_time=start_time,
            end_time=end_time,
            location=location if location else None,
            max_participants=max_participants if max_participants and max_participants > 0 else None
        )
        db.session.add(event)
        db.session.commit()
        
        flash(f'Événement "{title}" créé avec succès !', 'success')
        return redirect(url_for('events.event_detail', event_id=event.id))
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la création: {str(e)}', 'error')
        return redirect(url_for('events.new_event'))


@events_bp.route('/<int:event_id>')
def event_detail(event_id):
    """Show event details"""
    event = Event.query.get_or_404(event_id)
    
    is_participant = False
    is_creator = False
    conflicts = []
    
    if current_user.is_authenticated:
        is_creator = event.creator_id == current_user.id
        is_participant = EventParticipant.query.filter_by(
            event_id=event_id, 
            user_id=current_user.id
        ).first() is not None
        
        # Check for conflicts if not already participating
        if not is_participant:
            conflicts = check_schedule_conflicts(
                current_user, 
                event.day_of_week, 
                event.start_time, 
                event.end_time
            )
    
    return render_template(
        'events/detail.html',
        event=event,
        is_participant=is_participant,
        is_creator=is_creator,
        conflicts=conflicts
    )


@events_bp.route('/<int:event_id>/join', methods=['POST'])
@login_required
def join_event(event_id):
    """Join an event"""
    event = Event.query.get_or_404(event_id)
    
    # Check if already participating
    existing = EventParticipant.query.filter_by(
        event_id=event_id, 
        user_id=current_user.id
    ).first()
    
    if existing:
        flash('Vous participez déjà à cet événement', 'warning')
        return redirect(url_for('events.event_detail', event_id=event_id))
    
    # Check if full
    if event.is_full:
        flash('Cet événement est complet', 'warning')
        return redirect(url_for('events.event_detail', event_id=event_id))
    
    try:
        participant = EventParticipant(event_id=event_id, user_id=current_user.id)
        db.session.add(participant)
        db.session.commit()
        flash(f'Vous participez maintenant à "{event.title}" !', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur: {str(e)}', 'error')
    
    return redirect(url_for('events.event_detail', event_id=event_id))


@events_bp.route('/<int:event_id>/leave', methods=['POST'])
@login_required
def leave_event(event_id):
    """Leave an event"""
    participant = EventParticipant.query.filter_by(
        event_id=event_id, 
        user_id=current_user.id
    ).first()
    
    if not participant:
        flash('Vous ne participez pas à cet événement', 'warning')
        return redirect(url_for('events.event_detail', event_id=event_id))
    
    try:
        event_title = participant.event.title
        db.session.delete(participant)
        db.session.commit()
        flash(f'Vous ne participez plus à "{event_title}"', 'info')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur: {str(e)}', 'error')
    
    return redirect(url_for('events.list_events'))


@events_bp.route('/<int:event_id>/delete', methods=['POST'])
@login_required
def delete_event(event_id):
    """Delete an event (creator only)"""
    event = Event.query.get_or_404(event_id)
    
    if event.creator_id != current_user.id:
        flash('Action non autorisée', 'error')
        return redirect(url_for('events.event_detail', event_id=event_id))
    
    try:
        event_title = event.title
        db.session.delete(event)
        db.session.commit()
        flash(f'Événement "{event_title}" supprimé', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur: {str(e)}', 'error')
        return redirect(url_for('events.event_detail', event_id=event_id))
    
    return redirect(url_for('events.list_events'))
