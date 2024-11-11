# events/admin.py

from django.contrib import admin
from .models import  Donation,  HelpAlert 



admin.site.register(Donation)
admin.site.register(HelpAlert)



