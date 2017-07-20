from django.shortcuts import render
from django.db.models import Q
from django.urls import reverse
from . import models
from django.views.generic import CreateView
from .forms import ReviewForm


def books_by_genre(request, genre):
    tech_valleys = models.TechValleyTimes.objects.filter(book__genre=genre)
    books = models.Book.objects.filter(genre=genre).exclude(id__in=[tv.book.id for tv in tech_valleys])\
        .order_by('-rating')
    return render(request, 'products/bookGenreResult.html', {'books': books, 'genre': genre,
                                                             'tech_valleys': tech_valleys})


def get_book_by_author(request, author_id):
    author = models.Author.objects.filter(pk=author_id)
    books = models.Book.objects.filter(author_id=author_id)
    return render(request,'products/bookAuthorResult.html', {'books': books, 'author': author})


def get_book_by_rating(request):
    books = models.Book.objects.all().order_by('-rating')[0:25]
    return render(request, 'products/bookByRating.html', {'books': books})


def get_book_by_amount_sold(request):
    books = models.Book.objects.all().order_by('-amount_sold')[0:25]
    return render(request, 'products/topSellingBooks.html', {'books': books})


def get_tech_valley_books(request):
    tech_valleys = models.TechValleyTimes.objects.all()
    return render(request, 'products/bookResults.html', {'tech_valleys': tech_valleys})


def get_book_details(request,title):
    book = models.Book.objects.get(title=title)
    book_by_author = models.Book.objects.filter(author_id=book.author.id)
    reviews = models.Review.objects.filter(book_id=book.id)
    return render(request, 'products/bookDetail.html', {'book': book, 'book_by_author': book_by_author,
                                                        'reviews': reviews})


def search(request):
    search_request = request.GET.get('bookSearch')
    books = models.Book.objects.filter(
        Q(title__icontains=search_request) | Q(title__contains=search_request)
    )
    return render(request, 'products/bookSearchResult.html', {'books': books, 'search_request': search_request})


#########################################################################################################
##                                   REVIEW FUNCTIONS                                                  ##
########################################################################################################

class ReviewCreate(CreateView):
    template_name = 'products/bookReview.html'
    model = models.Review
    form_class = ReviewForm

    def form_valid(self,form):
        form.instance.user = self.request.user
        form.save()
        return super(ReviewCreate, self).form_valid(form)

    def get_success_url(self):
        return reverse('next')


