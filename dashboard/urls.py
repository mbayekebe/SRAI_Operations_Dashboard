from django.urls import path
from . import views

app_name = "dashboard"
urlpatterns = [
    path("", views.overview, name="overview"),
    path("unit/<str:code>/", views.unit_detail, name="unit_detail"),
    path("health.json", views.health_json, name="health_json"),
]
