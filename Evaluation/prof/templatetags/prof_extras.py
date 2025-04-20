from django import template
import json
from django.db.models import Avg

register = template.Library()

@register.filter(name='to_json')
def to_json(value):
    """Convert a value to JSON string"""
    return json.dumps(value)

@register.filter(name='moyenne_notes')
def moyenne_notes(notes):
    """Calculate average of notes"""
    if not notes:
        return 0
    return notes.aggregate(Avg('note'))['note__avg'] or 0