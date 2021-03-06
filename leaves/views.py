from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseBadRequest
from django.template import RequestContext
from django.core.mail import send_mail
from leaves.models import Leave
from django.contrib.auth.decorators import login_required
from fedup.email_settings import EMAIL_HOST_USER
import datetime
import re

@login_required
def read_create(request):
    if request.method == 'GET':
        leaves = Leave.objects.filter(user=request.user).order_by('-from_date')

        # Fetching leaves that need to be approved by the logged in user.
        unapproved = []
        for junior in request.user.supervisor.all():
            unapproved.extend(Leave.objects.filter(user=junior, approved=False))

        return render_to_response('leaves/index.html', 
                                    {'leaves': leaves, 'unapproved': unapproved}, 
                                    context_instance=RequestContext(request))
    elif request.method == 'POST':
        leave_text = request.POST.get('leave')
        if leave_text:
            leave = Leave()
            leave.user = request.user
            dates = re.findall('\d{2}/\d{2}/\d{2}', leave_text)
            if len(dates) > 0:
                leave.from_date = datetime.datetime.strptime(dates[0], '%d/%m/%y')
                leave_text = leave_text.replace(dates[0], '')
                try:
                    leave.to_date = datetime.datetime.strptime(dates[1], '%d/%m/%y')
                    leave_text = leave_text.replace(dates[1], '')
                except IndexError:
                    pass
                leave.reason = leave_text
                leave.save()
                supervisor = getattr(request.user.userprofile, 'supervisor')
                user_name = request.user.first_name + ' ' + request.user.last_name
                if supervisor:
                    if supervisor.email:
                        send_mail(
                                'Approve leave for {0}'.format(user_name),
                                '''{0} has requested for a leave from {1} to {2}.
Reason: {3}
To approve the leave please click on the link http://localhost:8000/leaves/{4}'''.format(
                                        user_name,
                                        dates[0], dates.pop(),
                                        leave.reason,
                                        leave.id
                                    ),
                                EMAIL_HOST_USER,
                                [supervisor.email]
                                )

                return HttpResponse('success')

        return HttpResponse('error')

@login_required
def read_update(request, leave_id=None):
    if leave_id is None:
        return HttpResponse('<h1>Not Found</h1>')

    leave = Leave.objects.get(id=leave_id)

    if request.method == "GET":
        return render_to_response('leaves/leave.html', 
                                    {'leave': leave}, 
                                    context_instance=RequestContext(request))

    elif request.method == "POST":
        approved = request.POST.get('approved', '')
        if approved == 'true':
            leave.approved = True
            if leave.user.userprofile in request.user.supervisor.all():
                leave.approved_by = request.user
                leave.approved_on = datetime.datetime.now()
                leave.save()

                send_mail(
                        'Your leave has been approved.',
                        'Your leave,\n {0}\n has been approved by {1} on {2}.'.format(
                                leave.reason,
                                leave.approved_by.first_name + ' ' + leave.approved_by.last_name,
                                leave.approved_on.date().isoformat()
                            ),
                        EMAIL_HOST_USER,
                        [request.user.email]
                        )
            else:
                return HttpResponseBadRequest('Sorry you are not authorized to approved this leave.')
        else:
            return HttpResponseBadRequest('Sorry, Leave once approved cannot be disapproved.')

        return HttpResponse('success')
