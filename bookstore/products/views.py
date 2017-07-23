from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.db.models import Q
from django.contrib import messages
from products.models import Review
from . import models
from accounts.models import User
from products.models import Book
from .forms import ReviewForm
from payments.models import Order, OrderItem


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


def get_book_details(request, title):
    book = models.Book.objects.get(title=title)
    book_by_author = models.Book.objects.filter(author_id=book.author.id)
    reviews = models.Review.objects.filter(book_id=book.id)

    if request.user.is_authenticated:
        # check if user purchased book
        allowed_to_review = purchased_book(book.id, request.user.user_id)
    else:
        allowed_to_review = False

    return render(request, 'products/bookDetail.html', {'book': book, 'book_by_author': book_by_author,
                                                        'reviews': reviews, 'allowed_to_review': allowed_to_review})


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
    # get url of current page and other parameters
    next = request.POST.get('next', '/')
    book_id = request.POST.get('book_id')
    user_id = request.user.user_id

    # check if user previously reviewed book
    check = user_left_review(user_id,book_id)
    print('CHECK IF user left a review : ' + str(check))
    if check:
        messages.error(request, 'You already left a review for this book.')
        return HttpResponseRedirect(next)

    print(request.POST)
    form = ReviewForm(request.POST)
    template_name = 'products/bookReview.html'

    if request.method == 'POST':
        if form.is_valid():
            # assign user id to review form
            review = form.save(commit=False)
            review.user = User.objects.get(user_id=user_id)
            review.book = Book.objects.get(id=book_id)
            review.save()

            messages.success(request, 'Review was submitted successfully.')
    else:
        form = ReviewForm()

    return HttpResponseRedirect(next)


# check is a user already reviewed the book
def user_left_review(user_id, book_id):
    try:
        Review.objects.get(user_id=user_id, book_id=book_id )

    except Review.DoesNotExist:
        return False

    return True


def purchased_book(book_id, user_id):
    all_purchased_orders = Order.objects.filter(user_id=user_id, payed_order=True)

    # the user has not purchased anything from book store
    if not all_purchased_orders:
        return False

    # search through each purchased order, check with book id if order item is in purchased order
    for order in all_purchased_orders:

        payed_book = OrderItem.objects.filter(order_id=order.id, book_id=book_id)

        # book has been found end for loop iteration
        if payed_book:
            return True

    return False
