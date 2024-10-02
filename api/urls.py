from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MindMapViewSet, NodeViewSet, register_user, login_user

router = DefaultRouter()
router.register(r'mindmaps', MindMapViewSet, basename='mindmap')
router.register(r'nodes', NodeViewSet, basename='node')

urlpatterns = [
    path('', include(router.urls)),
    path('register/', register_user, name='register'),
    path('login/', login_user, name='login'),
    path(
      'nodes/<str:pk>/auto_generate_children/',
      NodeViewSet.as_view({'post': 'auto_generate_children'}),
      name='node-auto-generate-children'
    ),
]