from django.db import models

# Create your models here.
class Process(models.Model):
    name=models.CharField(max_length=200)
    cycleTime=models.IntegerField()
    changeOverTime=models.IntegerField()

class Queue(models.Model):
    name=models.CharField(max_length=200)
    waitingTime=models.IntegerField(default=0)
    
