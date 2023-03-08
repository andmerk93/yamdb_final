from rest_framework import permissions

from users.models import ADMIN_ROLE


class IsAdminUser(permissions.BasePermission):

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and (request.user.role == ADMIN_ROLE or request.user.is_superuser)
        )


class CategoriesGenresTitlesPermissions(permissions.BasePermission):

    def has_permission(self, request, view):
        return request.method == 'GET' or (
            request.user.is_authenticated
            and (request.user.role == 'admin' or request.user.is_superuser)
        )


class ReviewsCommentsPermissions(permissions.IsAuthenticatedOrReadOnly):

    def has_object_permission(self, request, view, obj):
        if request.method == 'GET':
            return True
        if (
            request.method in ('PATCH', 'DELETE')
            and (
                obj.author == request.user
                or request.user.role in ('admin', 'moderator')
            )
        ):
            return True
