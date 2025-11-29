from rest_framework import serializers
from .models import Task


class TaskAnalyzeSerializer(serializers.Serializer):
    """
    Serializer for analyzing tasks without saving to DB.
    Does not require dependencies to be existing Task IDs.
    """
    id = serializers.IntegerField(required=False)
    title = serializers.CharField(max_length=255)
    due_date = serializers.DateField(required=False, allow_null=True)
    estimated_hours = serializers.FloatField()
    importance = serializers.IntegerField(min_value=1, max_value=10)
    dependencies = serializers.ListField(child=serializers.IntegerField(), required=False, default=list)
    priority_score = serializers.FloatField(read_only=True, required=False)


class TaskSerializer(serializers.ModelSerializer):
    # We add a read-only field for the calculated score
    priority_score = serializers.FloatField(read_only=True, required=False)
    
    class Meta:
        model = Task
        fields = ['id', 'title', 'due_date', 'estimated_hours', 'importance', 'dependencies', 'priority_score']