from rest_framework.serializers import ModelSerializer

from .models import Model_FlatSchedule


class FlatScheduleSerializer(ModelSerializer):
    class Meta:
        model = Model_FlatSchedule
        fields = '__all__'