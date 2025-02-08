from rest_framework import viewsets
from rest_framework.permissions import BasePermission, IsAuthenticatedOrReadOnly

from .models import News
from .serializers import NewsSerializer


class IsAuthorOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in ["GET", "HEAD"]:
            return True
        return request.user and (
            obj.author == request.user
            or request.user.is_staff
            or request.user.is_superuser
        )


class NewsViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    queryset = News.objects.all()
    serializer_class = NewsSerializer
