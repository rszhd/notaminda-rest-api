from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
  MindMapViewSet,
  NodeViewSet,
  PublicNodeViewSet,
  PublicMindMapViewSet,
  register_user,
  login_user,
  check_ai_api_key,
  chat_view
)

router = DefaultRouter()
router.register(r'mindmaps', MindMapViewSet, basename='mindmap')
router.register(r'nodes', NodeViewSet, basename='node')
router.register(r'public-mindmaps', PublicMindMapViewSet, basename='public_mindmap')
router.register(r'public-nodes', PublicNodeViewSet, basename='public_node')

urlpatterns = [
    path('', include(router.urls)),
    path('register/', register_user, name='register'),
    path('login/', login_user, name='login'),
    path('chat/', chat_view, name='chat_view'),
    path('check-ai-api-key/', check_ai_api_key, name='check_ai_api_key'),
    path(
      'nodes/<str:pk>/auto_generate_children/',
      NodeViewSet.as_view({'post': 'auto_generate_children'}),
      name='node-auto-generate-children'
    ),
    path(
      'nodes/<str:pk>/auto_generate_note/',
      NodeViewSet.as_view({'post': 'auto_generate_note'}),
      name='node-auto-generate-note'
    ),
]