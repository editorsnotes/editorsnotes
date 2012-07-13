from django import template
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from editorsnotes.main import utils
from editorsnotes.main.models import UserProfile
from isodate import datetime_isoformat
from lxml import etree

register = template.Library()

@register.filter
def as_text(tree):
    if tree is None:
        return ''
    return utils.xhtml_to_text(tree)

@register.filter
def as_html(tree):
    if tree is None:
        return ''
    return mark_safe(etree.tostring(tree))

@register.filter
def as_link(obj, fragment=''):
    return mark_safe(
        '<a class="model-link %s-link" href="%s%s">%s</a>' % (
            obj._meta.module_name, 
            obj.get_absolute_url(), fragment, 
            obj.as_html()))

@register.filter
def object_name(obj):
    return obj._meta.object_name

@register.filter
def timeago(datetime):
    utc_datetime = utils.naive_to_utc(datetime)
    return mark_safe(
        '<time class="timeago" datetime="%s">%s</time>' % (
            datetime_isoformat(utc_datetime), utc_datetime.strftime('%I:%M%p %Z, %b %d %Y')))

@register.filter
def display_last_updated(obj):
    if 'last_updated' in obj._meta.get_all_field_names():
        return mark_safe(
            '''<div class="last-updated">Last edited by %s %s.</div>''' % (
                as_link(UserProfile.get_for(obj.last_updater)), timeago(obj.last_updated)))
    else:
        return mark_safe(
            '''<div class="last-updated">Last edited by %s %s.</div>''' % (
                as_link(UserProfile.get_for(obj.creator)), timeago(obj.created)))

@register.filter
def display_edit_history(obj):
    return mark_safe(
        '''<div class="edit-history">
Created by %s %s.<br/>
Last edited by %s %s.</div>''' % (
            as_link(UserProfile.get_for(obj.creator)), timeago(obj.created),
            as_link(UserProfile.get_for(obj.last_updater)), timeago(obj.last_updated)))

@register.filter
def login_information(name):
    affiliation = UserProfile.get_for(name).affiliation
    if affiliation is not None:
        return mark_safe(
            'Logged in as %s (%s)' % (
            as_link(UserProfile.get_for(name)), as_link(affiliation)))
    else:
        return mark_safe(
            'Logged in as %s' % (
            as_link(UserProfile.get_for(name))))

@register.filter
def user_from_id(uid):
    return mark_safe(
        as_link(UserProfile.objects.get(user__id=uid)))
