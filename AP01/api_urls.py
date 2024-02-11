from django.urls import path, include
from rest_framework.routers import DefaultRouter

from AP01.views import ConversationViewSet

app_name = "AP01"

router = DefaultRouter()

router.register(r'conv', ConversationViewSet, basename='conversations')

urlpatterns = [
    path('', include(router.urls)),
    # You can add a custom route for creating prompts within conversations if needed.
]
