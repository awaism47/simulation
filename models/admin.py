from django.contrib import admin

# Register your models here.
from .models import Process, Queue

admin.site.register(Process)
admin.site.register(Queue)
