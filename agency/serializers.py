import requests
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from .models import SpyCat, Mission, Target


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
        if value not in VALID_BREEDS:
            raise ValidationError(f"{value} is not a recognized breed.")
        return value


class TargetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Target
        fields = '__all__'

    def validate(self, data):
        # Prevent updates to notes if the target is marked as complete
        if data.get('is_complete', False) and 'notes' in data:
            raise serializers.ValidationError("Cannot update notes for a completed target.")
        return data

    def update(self, instance, validated_data):
        # Prevent updating notes if target is complete
        if instance.is_complete:
            if 'notes' in validated_data:
                raise serializers.ValidationError(f"Cannot update notes on completed target '{instance.name}'")

        # Update target fields
        instance.name = validated_data.get('name', instance.name)
        instance.country = validated_data.get('country', instance.country)
        instance.notes = validated_data.get('notes', instance.notes)
        instance.is_complete = validated_data.get('is_complete', instance.is_complete)
        instance.save()
        return instance


class MissionSerializer(serializers.ModelSerializer):
    targets = TargetSerializer(many=True)

    class Meta:
        model = Mission
        fields = '__all__'

    def validate(self, data):
        targets = data.get('targets', [])
        if not (1 <= len(targets) <= 3):
            raise ValidationError("A mission must have between 1 and 3 targets.")
        return data

    def create(self, validated_data):
        targets_data = validated_data.pop('targets')
        mission = Mission.objects.create(**validated_data)

        # Create each target and associate it with the mission
        for target_data in targets_data:
            Target.objects.create(mission=mission, **target_data)
        return mission

    def update(self, instance, validated_data):
        # Prevent updating a completed mission
        if instance.is_complete:
            raise ValidationError("Cannot update a completed mission.")

        # Update mission fields (like cat assignment and complete status)
        instance.cat = validated_data.get('cat', instance.cat)
        instance.is_complete = validated_data.get('is_complete', instance.is_complete)
        instance.save()

        # Handle updates for targets
        targets_data = validated_data.get('targets', [])
        for target_data in targets_data:
            target_id = target_data.get('id')
            target_instance = Target.objects.get(id=target_id, mission=instance)
            TargetSerializer().update(target_instance, target_data)
        return instance
