from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^genre/(?P<genre>\w+)/$', views.books_by_genre, name='bookGenre'),
    url(r'^techValleyTimes/$', views.get_tech_valley_books, name='techValleyTimes'),
    url(r'^topRatedBooks/$', views.get_book_by_rating, name='topRatedBooks'),
    url(r'^topSellingBooks/$', views.get_book_by_amount_sold, name='topSellingBooks'),
    url(r'^bookDetail/(?P<title>.*)/$', views.get_book_details, name='bookDetail'),
    url(r'^review/$', views.ReviewCreate.as_view(), name='addBookReview'),
    url(r'^bookByAuthor/(?P<author_id>.*)/$', views.get_book_by_author, name='bookByAuthor'),
    url(r'search/$', views.search, name="search"),
]