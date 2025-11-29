from django.db import models

class Task(models.Model):
    title = models.CharField(max_length=255)
    due_date = models.DateField(null=True, blank=True)
    estimated_hours = models.PositiveIntegerField(help_text="Estimated time in hours")
    
    # Importance is a 1-10 scale [cite: 26]
    importance = models.IntegerField(
        choices=[(i, i) for i in range(1, 11)],
        default=5
    )
    
    # Dependencies: Tasks that must be completed BEFORE this one
    # symmetrical=False means if A depends on B, B does not necessarily depend on A
    dependencies = models.ManyToManyField('self', symmetrical=False, blank=True, related_name='required_by')

    def __str__(self):
        return self.title
