from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    MindMapViewSet,
    NodeViewSet,
    PublicNodeViewSet,
    PublicMindMapViewSet,
    register_user,
    login_user,
    verify_ai_key,
)

router = DefaultRouter()
router.register(r"mindmaps", MindMapViewSet, basename="mindmap")
router.register(r"nodes", NodeViewSet, basename="node")
router.register(r"public-mindmaps", PublicMindMapViewSet, basename="public_mindmap")
router.register(r"public-nodes", PublicNodeViewSet, basename="public_node")

urlpatterns = [
    path("", include(router.urls)),
    path("register/", register_user, name="register"),
    path("login/", login_user, name="login"),
    path("verify-ai-key/", verify_ai_key, name="verify_ai_key"),
    path(
        "nodes/<str:pk>/auto-generate-children/",
        NodeViewSet.as_view({"post": "auto_generate_children"}),
        name="node-auto-generate-children",
    ),
    path(
        "nodes/<str:pk>/auto-generate-note/",
        NodeViewSet.as_view({"post": "auto_generate_note"}),
        name="node-auto-generate-note",
    ),
]
