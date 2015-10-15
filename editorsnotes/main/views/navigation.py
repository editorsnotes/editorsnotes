# import os
# from random import randint
# 
# from django.conf import settings
# from django.contrib import messages
# from django.core.mail import mail_admins
# from django.http import (
#     HttpResponse, HttpResponseForbidden, HttpResponseRedirect)
# from django.shortcuts import render_to_response
# from django.template import RequestContext
# 
# from PIL import Image, ImageDraw, ImageFont
# 
# from ..forms import FeedbackForm
# 
# 
# def about_test(request):
#     x, y = (100, 38)
#     img = Image.new('RGBA', (x, y), (255, 255, 255))
#     draw = ImageDraw.Draw(img)
#     font = ImageFont.truetype(
#         os.path.join(settings.STATIC_ROOT, 'style', 'DejaVuSans-Bold.ttf'), 24)
#     i, s, j = (randint(10, 20), ('+', '-')[randint(0, 1)], randint(1, 9))
#     text = '%s %s %s' % (i, s, j)
# 
#     result = i + j if s == '+' else i - j
# 
#     draw.text((9, 5), text, (50, 50, 50), font=font)
# 
#     for i in xrange(0, 500):
#         draw.point((randint(0, x), randint(0, y)),
#                    [(xx, xx, xx) for xx in (randint(100, 180),)][0])
# 
#     request.session['test_answer'] = result
# 
#     response = HttpResponse(content_type="image/png")
#     img.save(response, 'PNG')
# 
#     return response
# 
# 
# def about(request):
#     o = {}
# 
#     if request.method == 'POST':
# 
#         bad_answers = request.session.setdefault('bad_answers', 0)
#         if bad_answers > 3:
#             return HttpResponseForbidden(
#                 'Too many failed attempts. Try again later.')
# 
#         o['form'] = FeedbackForm(request.POST)
#         if o['form'].is_valid():
# 
#             test_answer = request.POST.get('testanswer', '')
#             is_good_answer = (
#                 test_answer.isdigit() and
#                 int(test_answer) == request.session['test_answer']
#             )
#             if is_good_answer:
#                 request.session.pop('bad_answers')
# 
#                 choice = o['form'].cleaned_data['purpose']
#                 subj = '(%s) %s' % (
#                     dict(o['form'].fields['purpose'].choices)[choice],
#                     o['form'].cleaned_data['name'])
#                 msg = 'reply to: {email}\n\n{message}'.format(
#                     **o['form'].cleaned_data)
#                 mail_admins(subj, msg, fail_silently=True)
#                 messages.add_message(
#                     request, messages.SUCCESS,
#                     'Thank you. Your feedback has been submitted.')
#                 return HttpResponseRedirect('/about/')
#             else:
#                 request.session['bad_answers'] = bad_answers + 1
#                 o['bad_answer'] = True
#                 return render_to_response(
#                     'about.html', o, context_instance=RequestContext(request))
#     else:
#         o['form'] = FeedbackForm()
#     return render_to_response(
#         'about.html', o, context_instance=RequestContext(request))
