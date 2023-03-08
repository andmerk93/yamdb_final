import hashlib
from datetime import datetime, timedelta
from string import ascii_letters, digits

from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from django.utils.crypto import get_random_string

from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.response import Response

from rest_framework_simplejwt.tokens import RefreshToken

from django_filters.rest_framework import DjangoFilterBackend

from api.filters import FilterTitle
from api.mixins import CreateListDestroyViewSet
from api.serializers import (CategorySerializer,
                             CommentSerializer,
                             GenreSerializer,
                             GetTitleSerializer,
                             ReviewSerializer,
                             TitleSerializer,
                             UserSerializer)
from api.permissions import (CategoriesGenresTitlesPermissions,
                             ReviewsCommentsPermissions,
                             IsAdminUser)
from reviews.models import Category, Comment, Genre, Review, Title

from users.models import ConfCode, User


class AbstractViewSet(CreateListDestroyViewSet):
    lookup_field = 'slug'
    permission_classes = (CategoriesGenresTitlesPermissions,)
    filter_backends = (SearchFilter,)
    search_fields = ('name',)


class GenreViewSet(AbstractViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer


class CategoryViewSet(AbstractViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class TitleViewSet(viewsets.ModelViewSet):
    queryset = Title.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filterset_class = FilterTitle
    permission_classes = (CategoriesGenresTitlesPermissions,)

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return GetTitleSerializer
        return TitleSerializer


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = (ReviewsCommentsPermissions,)

    def get_queryset(self):
        title = get_object_or_404(Title, pk=self.kwargs.get('title_id'))
        new_queryset = title.reviews.all()
        return new_queryset

    def perform_create(self, serializer):
        title = get_object_or_404(Title, pk=self.kwargs.get('title_id'))

        serializer.save(
            author=self.request.user,
            title=title
        )

    def perform_update(self, serializer):
        title = get_object_or_404(Title, pk=self.kwargs.get('title_id'))
        review_id = self.kwargs.get('pk')
        author = Review.objects.get(pk=review_id).author
        serializer.save(
            author=author,
            title_id=title.id
        )


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = (ReviewsCommentsPermissions,)

    def get_review(self):
        return get_object_or_404(Review, pk=self.kwargs.get('review_id'))

    def get_queryset(self):
        review = self.get_review()
        new_queryset = review.comments.all()
        return new_queryset

    def perform_create(self, serializer):
        review = self.get_review()
        serializer.save(author=self.request.user, review_id=review.id)

    def perform_update(self, serializer):
        review = self.get_review()
        comment_id = self.kwargs.get('pk')
        author = Comment.objects.get(pk=comment_id).author
        serializer.save(
            author=author,
            review_id=review.id
        )


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = 'username'
    filter_backends = (SearchFilter,)
    search_fields = ('username',)
    http_method_names = ['get', 'post', 'patch', 'delete']
    permission_classes = (IsAdminUser,)

    @action(
        detail=False,
        methods=['get', 'patch'],
        url_path='me',
        permission_classes=(permissions.IsAuthenticated,)
    )
    def me(self, request, *args, **kwargs):
        self.object = get_object_or_404(User, pk=request.user.id)
        if request.method == 'PATCH':
            serializer = self.get_serializer(
                self.object,
                data=request.data,
                partial=True
            )
            serializer.is_valid(raise_exception=True)
            if (
                'role' in request.data
                and request.data['role'] != self.object.role
            ):
                return Response(
                    request.data,
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer.save()
        else:
            serializer = self.get_serializer(self.object)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SignupView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (permissions.AllowAny,)

    def create(self, request, *args, **kwargs):
        if (
            'username' not in request.data
            or 'email'not in request.data
        ):
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
        username = request.data['username']
        email = request.data['email']
        if username == 'me':
            return Response(
                data=request.data,
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer = self.get_serializer(data=request.data)
        if not User.objects.filter(
            username=username,
            email=email
        ).exists():
            serializer.is_valid(raise_exception=True)
            serializer.save()
        secret_key = get_random_string(20, ascii_letters + digits) + username
        secret_hash = hashlib.sha256((secret_key).encode('utf-8')).hexdigest()
        send_mail(
            subject='YamDB Confirmation code',
            message=f'Confirmation code: {secret_hash}',
            from_email='YamDB@example.com',
            recipient_list=[email],
            fail_silently=False,
        )
        ConfCode.objects.update_or_create(
            user=User.objects.get(username=username),
            defaults={
                'code': secret_hash,
                'expires': datetime.utcnow() + timedelta(days=1),
            }
        )
        return Response(request.data, status=status.HTTP_200_OK)


class TokenView(generics.CreateAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = UserSerializer

    def create(self, request, *args, **kwargs):
        if (
            'username' not in request.data
            or 'confirmation_code'not in request.data
        ):
            return Response(request.data, status=status.HTTP_400_BAD_REQUEST)
        user = get_object_or_404(User, username=request.data['username'])
        if (
            user.conf_code.code != request.data['confirmation_code']
            or user.conf_code.expires < datetime.utcnow()
        ):
            return Response(request.data, status=status.HTTP_400_BAD_REQUEST)
        token = RefreshToken.for_user(user)
        return Response(
            data={'token': str(token.access_token)},
            status=status.HTTP_200_OK
        )
