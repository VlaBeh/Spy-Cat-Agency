from django.core.exceptions import ValidationError
from django.db import models


class SpyCat(models.Model):
    BREEDS = [
        ('Persian', 'Persian'),
        ('Siamese', 'Siamese'),
        ('Bengal', 'Bengal'),
        ('Sphynx', 'Sphynx'),
    ]
    name = models.CharField(max_length=100)
    years_of_experience = models.PositiveIntegerField()
    breed = models.CharField(max_length=50)
    salary = models.PositiveIntegerField()

    def __str__(self):
        return self.name


class Mission(models.Model):
    cat = models.OneToOneField(
        SpyCat, null=True, blank=True, on_delete=models.SET_NULL, related_name='mission'
    )
    is_complete = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.pk and not (1 <= self.targets.count <= 3):
            raise ValidationError('Mission must have between 1 and 3 targets')
        super().save(*args, **kwargs)

    def check_is_complete(self):
        if all(target.is_complete for target in self.targets.all()):
            self.is_complete = True
            self.save()

    def __str__(self):
        return f"Mission for {self.cat.name if self.cat else 'Unassigned'}"


class Target(models.Model):
    mission = models.ForeignKey(Mission, related_name='targets', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    notes = models.TextField(blank=True)
    is_complete = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.is_complete and self.pk:
            original = Target.objects.get(pk=self.pk)
            if original.notes != self.notes:
                self.notes = original.notes

        super().save(*args, **kwargs)
        self.mission.check_is_complete()

    def __str__(self):
        return f"Target {self.name} in {self.country}"
