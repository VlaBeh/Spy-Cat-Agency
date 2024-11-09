from django.urls import path, include
from agency.views import *
from rest_framework import routers

app_name = "sca"

router = routers.DefaultRouter()

router.register("cats", SpyCatViewSet)
router.register("mission", MissionViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
