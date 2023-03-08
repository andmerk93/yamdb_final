from csv import DictReader

from django.core.management.base import BaseCommand

from reviews.models import Category, Comment, Genre, GenreTitle, Review, Title
from users.models import User


FILES = [
    ('static/data/users.csv', User),
    ('static/data/category.csv', Category),
    ('static/data/genre.csv', Genre),
    ('static/data/genre_title.csv', GenreTitle)
]


class Command(BaseCommand):

    def reader(self, file, object):
        for row in DictReader(open(file, 'r', encoding='utf-8')):
            object(**row).save()

    def handle(self, *args, **options):
        for i in range(2):
            self.reader(*FILES[i])
        with open('static/data/titles.csv', 'r', encoding='utf-8') as inp_f:
            reader = DictReader(inp_f)
            for row in reader:
                titles = Title(
                    id=row['id'],
                    name=row['name'],
                    year=row['year'],
                    category=Category.objects.get(pk=row['category'])
                )
                titles.save()
        self.reader(*FILES[3])
        with open('static/data/review.csv', 'r', encoding='utf-8') as inp_f:
            reader = DictReader(inp_f)
            for row in reader:
                review = Review(
                    id=row['id'],
                    title_id=row['title_id'],
                    text=row['text'],
                    author_id=row['author'],
                    score=row['score'],
                    pub_date=row['pub_date'],
                )
                review.save()
        with open('static/data/comments.csv', 'r', encoding='utf-8') as inp_f:
            reader = DictReader(inp_f)
            for row in reader:
                comments = Comment(
                    id=row['id'],
                    review_id=row['review_id'],
                    text=row['text'],
                    author=User.objects.get(pk=row['author']),
                    pub_date=row['pub_date'],
                )
                comments.save()
