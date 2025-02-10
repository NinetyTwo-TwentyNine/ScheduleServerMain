from django.contrib.postgres.fields import ArrayField
from djongo import models

# Create your models here.

class Model_IntString(models.Model):
    id = models.IntegerField(primary_key=True)
    title = models.TextField()

    class Meta:
        ordering = ['-id']

class Model_IntDate(models.Model):
    id = models.IntegerField(primary_key=True)
    date = models.DateField()

    class Meta:
        ordering = ['-id']

class Model_IntArray(models.Model):
        specialId = models.IntegerField(primary_key=True)
        scheduleId = ArrayField(base_field=models.IntegerField(),blank=True,default=list)

        class Meta:
            ordering = ['-specialId']

class Model_IntIntIntArrayArray(models.Model):
    specialId = models.IntegerField(primary_key=True)
    scheduleId = models.IntegerField()
    pairNum = models.IntegerField()
    subPairs = ArrayField(models.IntegerField(), blank=True, default=list)
    subGroups = ArrayField(models.IntegerField(), blank=True, default=list)

    class Meta:
        ordering = ['-specialId']

class Model_FlatScheduleParameters(models.Model):
    _id = models.IntegerField(primary_key=True)
    cabinetList = models.ArrayField(model_container=Model_IntString)
    groupList = models.ArrayField(model_container=Model_IntString)
    lessonList = models.ArrayField(model_container=Model_IntString)
    teacherList = models.ArrayField(model_container=Model_IntString)
    dayList = models.ArrayField(model_container=Model_IntDate)

    class Meta:
        ordering = ['-_id']

class Model_FlatScheduleDetailed(models.Model):
    _id = models.IntegerField(primary_key=True)
    scheduleDay = models.ArrayField(model_container=Model_IntArray)
    scheduleGroup = models.ArrayField(model_container=Model_IntArray)
    scheduleLesson = models.ArrayField(model_container=Model_IntIntIntArrayArray)
    cabinetLesson = models.ArrayField(model_container=Model_IntIntIntArrayArray)
    teacherLesson = models.ArrayField(model_container=Model_IntIntIntArrayArray)
    version = models.IntegerField()

    class Meta:
        ordering = ['-_id']

class Model_FlatScheduleBase(models.Model):
    _id = models.IntegerField(primary_key=True)
    nameList = models.ArrayField(model_container=Model_IntString)
    scheduleName = models.ArrayField(model_container=Model_IntArray)
    scheduleDay = models.ArrayField(model_container=Model_IntArray)
    scheduleGroup = models.ArrayField(model_container=Model_IntArray)
    scheduleLesson = models.ArrayField(model_container=Model_IntIntIntArrayArray)
    cabinetLesson = models.ArrayField(model_container=Model_IntIntIntArrayArray)
    teacherLesson = models.ArrayField(model_container=Model_IntIntIntArrayArray)

    class Meta:
        ordering = ['-_id']

class Model_FlatSchedule(models.Model):
    _id = models.IntegerField(auto_created=True,primary_key=True)
    BaseParameters = models.ArrayField(model_container=Model_FlatScheduleParameters, max_length=1)
    BaseSchedules = models.ArrayField(model_container=Model_FlatScheduleBase, max_length=1)
    CurrentSchedules = models.ArrayField(model_container=Model_FlatScheduleDetailed, max_length=1)

    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-updated']
        db_table = "collection_schedule_main"