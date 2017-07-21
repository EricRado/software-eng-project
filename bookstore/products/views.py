from django.core.checks import messages
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.db.models import Q
from django.urls import reverse
from . import models
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

def get_review_form(request):
    # get url of current page
    next = request.POST.get('next', '/')
    form = ReviewForm(request.POST)
    template_name = 'products/bookReview.html'

    print('I am currently running this function!!!')

    if not request.user.is_authenticated():
        messages.error(request, 'Please login first to review book.')
        return HttpResponseRedirect(next)

    if request.method == 'POST':
        if form.is_valid:
            # assign user id to review form
            form.instance.user = request.user
            form.save()
    else:
        form = ReviewForm()

    return HttpResponseRedirect(next)




