from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from .models import SpyCat, Mission, Target
import requests


def fetch_valid_breeds():
    try:
        response = requests.get("https://api.thecatapi.com/v1/breeds")
        response.raise_for_status()
        return [breed["name"] for breed in response.json()]
    except requests.RequestException:
        return []


VALID_BREEDS = fetch_valid_breeds()


class SpyCatSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpyCat
        fields = '__all__'

    def validate_breed(self, value):
        """Validate breed against a list of valid breeds from The Cat API."""
        if value not in VALID_BREEDS:
            raise ValidationError(f"{value} is not a recognized breed.")
        return value


class TargetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Target
        fields = '__all__'

    def validate(self, data):
        """Ensure that notes cannot be updated for completed targets."""
        if data.get('is_complete', False) and 'notes' in data:
            raise ValidationError("Cannot update notes for a completed target.")
        return data


class MissionSerializer(serializers.ModelSerializer):
    # Use PrimaryKeyRelatedField for associating targets with the mission
    targets = serializers.PrimaryKeyRelatedField(many=True, queryset=Target.objects.all())

    class Meta:
        model = Mission
        fields = '__all__'

    def validate(self, data):
        """Ensure that a mission has between 1 and 3 targets."""
        targets_data = data.get('targets', [])
        if not (1 <= len(targets_data) <= 3):
            raise ValidationError("A mission must have between 1 and 3 targets.")
        return data

    def create(self, validated_data):
        """Create a mission and associate targets with it."""
        targets_data = validated_data.pop('targets')  # Extract targets from validated data
        mission = Mission.objects.create(**validated_data)  # Create mission without targets

        # Associate targets with the mission
        for target_data in targets_data:
            mission.targets.add(target_data)

        mission.save()
        return mission
