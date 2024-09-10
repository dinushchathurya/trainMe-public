from django.contrib import admin
from . import models
import inspect

for name, obj in inspect.getmembers(models):
    if inspect.isclass(obj) and issubclass(obj, models.models.Model):
        admin.site.register(obj)