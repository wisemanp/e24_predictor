from django.db import models

class Runner(models.Model):
    name = models.CharField(max_length=100)

class Lap(models.Model):
    number = models.PositiveIntegerField()
    start_time = models.DateTimeField(null=True, blank=True)
    runner = models.ForeignKey(Runner, on_delete=models.SET_NULL, null=True, blank=True)
    laptime = models.DurationField(null=True, blank=True)
    pace = models.CharField(max_length=20, null=True, blank=True)
    total_time = models.DurationField(null=True, blank=True)
    fixed = models.BooleanField(default=False)  # True if fetched from the official website
