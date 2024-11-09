from http import HTTPStatus

from rest_framework import status, views, viewsets
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework.decorators import action
from .models import SpyCat, Mission, Target
from .serializers import MissionSerializer, TargetSerializer, SpyCatSerializer
import requests


def fetch_valid_breeds():
    try:
        response = requests.get("https://api.thecatapi.com/v1/breeds")
        response.raise_for_status()
        return [breed["name"] for breed in response.json()]
    except requests.RequestException:
        return []


VALID_BREEDS = fetch_valid_breeds()


class SpyCatViewSet(viewsets.ModelViewSet):
    queryset = SpyCat.objects.all()
    serializer_class = SpyCatSerializer

    def create(self, request, *args, **kwargs):
        breed = request.data.get('breed', '')
        if breed not in VALID_BREEDS:
            raise ValidationError(f"{breed} is not a valid breed.")

        return super().create(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def update_salary(self, request):
        """Update the salary of a spy cat"""
        spy_cat = self.get_object()
        new_salary = request.data.get('salary', None)
        if new_salary is not None:
            spy_cat.salary = new_salary
            spy_cat.save()
            return Response(SpyCatSerializer(spy_cat).data)
        else:
            return Response({"error": "Salary is required to update."}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['delete'])
    def remove(self, request, pk=None):
        """Remove a spy cat from the system"""
        spy_cat = self.get_object()
        spy_cat.delete()
        return Response({"message": "Spy cat removed successfully."}, status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'])
    def list_all(self, request):
        """List all spy cats"""
        spy_cats = SpyCat.objects.all()
        serializer = SpyCatSerializer(spy_cats, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def get_single(self, request):
        """Get a single spy cat"""
        spy_cat = self.get_object()
        serializer = SpyCatSerializer(spy_cat)
        return Response(serializer.data)


class TargetViewSet(viewsets.ModelViewSet):
    queryset = Target.objects.all()
    serializer_class = TargetSerializer

    @action(detail=True, methods=['post'])
    def mark_complete(self, request):
        """Mark target as complete"""
        target = self.get_object()
        if target.is_complete:
            raise ValidationError("Target is already marked as complete.")
        target.is_complete = True
        target.save()
        return Response(TargetSerializer(target).data)

    @action(detail=True, methods=['post'])
    def update_notes(self, request):
        """Update notes for a target if not completed"""
        target = self.get_object()
        if target.is_complete:
            raise ValidationError("Cannot update notes for a completed target.")
        target.notes = request.data.get('notes', target.notes)
        target.save()
        return Response(TargetSerializer(target).data)


class MissionViewSet(viewsets.ModelViewSet):
    @action(detail=False, methods=['post'])
    def create_mission(self, request):
        """Create a mission with targets"""
        data = request.data
        targets_data = data.get('targets', [])
        if not (1 <= len(targets_data) <= 3):
            return Response({"error": "A mission must have between 1 and 3 targets."},
                            status=status.HTTP_400_BAD_REQUEST)
        breed = data.get('cat', {}).get('breed', '')
        if breed not in self.VALID_BREEDS:
            return Response({"error": f"{breed} is not a valid breed."}, status=status.HTTP_400_BAD_REQUEST)
        mission_serializer = MissionSerializer(data=data)
        if mission_serializer.is_valid():
            mission = mission_serializer.save()
            # Create Targets
            for target_data in targets_data:
                target_data['mission'] = mission.id
                TargetSerializer(data=target_data).is_valid(raise_exception=True)
                Target.objects.create(**target_data)

            return Response(mission_serializer.data, status=status.HTTP_201_CREATED)
        return Response(mission_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def list_missions(self, request):
        missions = Mission.objects.all()
        serializer = MissionSerializer(missions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def get_mission(self, request, pk=None):
        """Retrieve a single mission"""
        try:
            mission = Mission.objects.get(pk=pk)
        except Mission.DoesNotExist:
            return Response({"error": "Mission not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = MissionSerializer(mission)
        return Response(serializer.data)

    @action(detail=True, methods=['delete'])
    def delete_mission(self, request, pk=None):
        """Delete a mission, but it cannot be deleted if assigned to a cat"""
        try:
            mission = Mission.objects.get(pk=pk)
        except Mission.DoesNotExist:
            return Response({"error": "Mission not found."}, status=status.HTTP_404_NOT_FOUND)

        if mission.cat:
            return Response({"error": "Cannot delete a mission that is assigned to a cat."},
                            status=status.HTTP_400_BAD_REQUEST)

        mission.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['put'])
    def update_mission(self, request, pk=None):
        """If Mission is completed we cannot update the mission"""
        try:
            mission = Mission.objects.get(pk=pk)
        except Mission.DoesNotExist:
            return Response({"error": "Mission not found."}, status=status.HTTP_404_NOT_FOUND)
        if mission.is_complete:
            return Response({"error": "Cannot update a completed mission."}, status=status.HTTP_400_BAD_REQUEST)

    def update_mission_field(self, request, mission):
        mission_serializer = MissionSerializer(mission, data=request.data, partial=True)
        if mission_serializer.is_valid():
            mission_serializer.save()

    def update_targets(self, request, mission, mission_serializer):
        targets_data = request.data.get('targets', [])
        for target_data in targets_data:
            target_instance = Target.objects.get(id=target_data['id'], mission=mission)
            if target_instance.is_complete:
                return Response({"error": f"Cannot update a completed target: {target_instance.name}"},
                                status=status.HTTP_400_BAD_REQUEST)
            target_serializer = TargetSerializer(target_instance, data=target_data, partial=True)
            if target_serializer.is_valid():
                target_serializer.save()
            else:
                return Response(target_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            return Response(mission_serializer.data)
        return Response(mission_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['put'])
    def assign_cat(self, request, pk=None):
        """Assign a cat to the mission"""
        try:
            mission = Mission.objects.get(pk=pk)
        except Mission.DoesNotExist:
            return Response({"error": "Mission not found."}, status=status.HTTP_404_NOT_FOUND)

        # If mission is complete, we cannot assign a cat
        if mission.is_complete:
            return Response({"error": "Cannot assign a cat to a completed mission."},
                            status=status.HTTP_400_BAD_REQUEST)

        cat_data = request.data.get('cat')
        try:
            cat = SpyCat.objects.get(id=cat_data['id'])
        except SpyCat.DoesNotExist:
            return Response({"error": "Cat not found."}, status=status.HTTP_404_NOT_FOUND)

        # Ensure the cat doesn't already have a mission
        if cat.mission:
            return Response({"error": "This cat is already assigned to another mission."},
                            status=status.HTTP_400_BAD_REQUEST)
        mission.cat = cat
        mission.save()

        return Response(MissionSerializer(mission).data)