from django.db import models
from django.core.exceptions import ValidationError
import requests


class SpyCat(models.Model):
    name = models.CharField(max_length=100)
    years_experience = models.IntegerField()
    breed = models.CharField(max_length=100)
    salary = models.DecimalField(max_digits=10, decimal_places=2)

    def clean(self):
        # Validate breed with TheCatAPI
        response = requests.get("https://api.thecatapi.com/v1/breeds")
        if response.status_code == 200:
            breeds = [breed['name'] for breed in response.json()]
            if self.breed not in breeds:
                raise ValidationError(f"{self.breed} is not a recognized breed.")
        else:
            raise ValidationError("Unable to validate breed. Please try again later.")

    def __str__(self):
        return self.name


class Mission(models.Model):
    cat = models.OneToOneField(SpyCat, on_delete=models.SET_NULL, null=True, blank=True)
    is_complete = models.BooleanField(default=False)

    def check_is_complete(self):
        # Mark mission as complete if all targets are complete
        if all(target.is_complete for target in self.target_set.all()):
            self.is_complete = True
            self.save()

    def delete(self, *args, **kwargs):
        if self.cat is not None:
            raise ValidationError("Cannot delete a mission that is assigned to a cat.")
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"Mission {self.id} - {'Complete' if self.is_complete else 'Incomplete'}"


class Target(models.Model):
    mission = models.ForeignKey(Mission, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    notes = models.TextField()
    is_complete = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.is_complete:
            # Freeze notes if the target is complete
            self.notes = self.notes
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
