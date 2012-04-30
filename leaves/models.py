from django.db import models
from django.contrib.auth.models import User
from django.contrib import admin

class Leave(models.Model):
    user = models.ForeignKey(User)
    from_date = models.DateField()
    to_date = models.DateField(null=True, blank=True)
    reason = models.CharField(max_length=200)
    approved = models.BooleanField(default=False)

    def __unicode__(self):
        return self.reason

admin.site.register(Leave)
