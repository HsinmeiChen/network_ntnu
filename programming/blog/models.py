from django.db import models

class TeachingSession(models.Model):
    user_id = models.CharField(max_length=100, unique=True)
    current_step = models.IntegerField(default=0)
    total_steps = models.IntegerField(default=0)  # 新增欄位，預設值設為 0

    def __str__(self):
        return self.user_id
