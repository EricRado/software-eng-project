import decimal
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.csrf import csrf_protect
from django.views.generic import CreateView, DeleteView
from .forms import CreditCardForm
from products.models import Book
from .models import OrderItem, Order, CreditCard, FutureOrderItem
from django.shortcuts import get_object_or_404
from django.contrib import messages


#########################################################################################################
##                                   CREDIT CARD FUNCTIONS                                            ##
########################################################################################################


def display_credit_cards(request):
    online_user = request.user
    cards = CreditCard.objects.filter(user_id=online_user.user_id)
    return render(request, 'payments/displayCreditCards.html', {'cards': cards})


class CreditCardCreate(CreateView):
    template_name = 'payments/addCreditCard.html'
    model = CreditCard
    form_class = CreditCardForm

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.save()
        return super(CreditCardCreate, self).form_valid(form)

    def get_success_url(self):
        messages.success(self.request, 'Credit Card has been successfully added.')
        return reverse('payments:displayCC')


class CreditCardDelete(DeleteView):
    model = CreditCard

    def get_success_url(self):
        messages.success(self.request, 'Credit Card has been successfully removed.')
        return reverse('payments:displayCC')

    def get_object(self):
        cc_id = self.request.POST.get('cc_id')
        return get_object_or_404(CreditCard, pk=cc_id)


@csrf_protect
def manage_credit_card(request):
    cc_id = request.GET.get("cc_id")
    cc = CreditCard.objects.get(pk=cc_id)
    form = CreditCardForm(request.POST or None, initial={'name_on_card': cc.name_on_card, 'cc_number': cc.cc_number,
                                                             'security_code': cc.security_code, 'expiration': cc.expiration})

    if request.method == 'POST':
        if form.is_valid():
            cc.name_on_card = form.cleaned_data['name_on_card']
            cc.cc_number = form.cleaned_data['cc_number']
            cc.security_code = form.cleaned_data['security_code']
            cc.expiration = form.cleaned_data['expiration']

            cc.save()

            messages.success(request, 'Credit Card was successfully updated.')

            return HttpResponseRedirect(reverse('payments:displayCC'))

    else:
        form = CreditCardForm(instance=cc)

    return render(request, 'payments/updateCreditCard.html', {'form': form})


#########################################################################################################
##                                   SHOPPING CART FUNCTIONS                                           ##
########################################################################################################

def display_shopping_cart(request):
    # get shopping cart id
    order_id = request.session['orderId']

    # get future cart id
    f_order_id = request.session['fOrderId']

    order_items = OrderItem.objects.filter(order_id=order_id)
    future_order_items = FutureOrderItem.objects.filter(future_order_id=f_order_id)
    shopping_cart = Order.objects.filter(pk=order_id)

    return render(request, 'payments/shoppingCart.html', {'order_items': order_items, 'shopping_cart': shopping_cart,
                                                          'future_order_items': future_order_items})


def add_book_to_cart(request):
    # get url of current page
    next = request.POST.get('next', '/')

    # verify if a user is in session or redirect with a login message
    if not request.user.is_authenticated():
        messages.error(request, 'Please login first to add books to the shopping cart.')
        return HttpResponseRedirect(next)

    # get parameters from quantity form
    quantity = request.POST.get('quantity')
    book_id = request.POST.get('bookId')

    # get book with id
    book = Book.objects.get(pk=book_id)
    price = book.price

    # check if book is in stock or meets the demand of the user
    in_stock_msg = check_book_stock(book, quantity)

    if in_stock_msg:
        messages.error(request, in_stock_msg)
        return HttpResponseRedirect(next)

    # get online user shopping cart id
    order_id = request.session['orderId']

    # find total price of quantity of specific book
    book_added_price = float(quantity) * float(price)

    # check if book has already been added to shopping cart
    try:

        book_order_exists = OrderItem.objects.get(order_id=order_id, book_id=book_id)
        book_order_exists.quantity += int(quantity)
        book_order_exists.book_price_quantity += decimal.Decimal(book_added_price)
        book_order_exists.save()

    except OrderItem.DoesNotExist:

        # add order item to database
        add_book = OrderItem.objects.create(quantity=quantity, book_id=book_id, order_id=order_id,
                                            book_price_quantity=book_added_price)
        add_book.save()

    # update order price, tax price, and total price
    update_cart_price(order_id, book_added_price)

    messages.success(request, book.title + ' was successfully added to shopping cart.')

    return HttpResponseRedirect(next)


def remove_book_from_cart(request):
    order_item_id = request.GET.get('order_item_id')

    # get online user shopping cart id
    order_id = request.session['orderId']

    # get book item to remove from shopping cart
    book_order_item = get_object_or_404(OrderItem, pk=order_item_id)

    # update order total by removing price of books removed by the user
    update_removed_book_cart_price(order_id, book_order_item.book_price_quantity)

    messages.success(request, book_order_item.book.title + ' was successfully removed from shopping cart.')

    book_order_item.delete()

    return HttpResponseRedirect(reverse('payments:shoppingCart'))


def update_from_shopping_cart_page(request):
    new_quantity = request.POST.get('quantity')
    order_item_id = request.POST.get('order_item_id')
    order_id = request.session['orderId']

    # get the order item of the book that is going to be updated
    order_item = OrderItem.objects.get(pk=order_item_id)

    # check if quantity in stock meets demand
    in_stock_msg = check_book_stock(order_item.book, new_quantity)
    if in_stock_msg:
        messages.error(request, in_stock_msg)
        return HttpResponseRedirect(reverse('payments:shoppingCart'))

    # store previous quantity user wanted
    previous_quantity = order_item.quantity

    # update book order item with new quantity and total quantity price
    order_item.book_price_quantity = order_item.book.price * decimal.Decimal(new_quantity)
    order_item.quantity = int(new_quantity)
    order_item.save()

    # check if new quantity is greater or less than previous quantity amount and then update shopping cart price
    if int(new_quantity) < previous_quantity:
        book_removed_price = (previous_quantity - int(new_quantity)) * order_item.book.price
        update_removed_book_cart_price(order_id, book_removed_price)
    else:
        book_added_price = (int(new_quantity) - previous_quantity) * order_item.book.price
        update_cart_price(order_id, book_added_price)

    messages.success(request, order_item.book.title + ' new quantity was successfully updated.')

    return HttpResponseRedirect(reverse('payments:shoppingCart'))


# when a book is removed from shopping cart or book quantity has decreased, update the new total price
def update_removed_book_cart_price(order_id, book_removed_price):
    order = Order.objects.get(pk=order_id)

    # update price of order not including taxes
    order.price -= decimal.Decimal(book_removed_price)

    # update tax price of order
    order.tax_price -= decimal.Decimal(book_removed_price) * decimal.Decimal(0.07)

    # update total price of order
    order.total_price -= decimal.Decimal(book_removed_price) \
                         + decimal.Decimal(book_removed_price) * decimal.Decimal(0.07)

    order.save()


# updates book cart price if added to shopping cart or quantity has increased, update the new total price
def update_cart_price(order_id, book_added_price):
    order = Order.objects.get(pk=order_id)

    # update price of order not including taxes
    order.price += decimal.Decimal(book_added_price)

    # update tax price of order
    order.tax_price += decimal.Decimal(book_added_price) * decimal.Decimal(0.07)

    # update total price of order
    order.total_price += decimal.Decimal(book_added_price) + decimal.Decimal(book_added_price) * decimal.Decimal(0.07)

    order.save()


def check_book_stock(book, quantity):
    if book.quantity == 0:
        return 'Sorry, we are out of stock.'

    if book.quantity < int(quantity):
        return "Sorry, we don't have enough copies in stock to meet your demand."

    return ''


#########################################################################################################
##                                   FUTURE ORDER FUNCTIONS                                           ##
########################################################################################################

def add_future_order_item(request):
    # get url from current page
    next = request.POST.get('next', '/')

    # verify if a user is in session or redirect with a login message
    if not request.user.is_authenticated():
        messages.error(request, 'Please login first to add books to a future order.')
        return HttpResponseRedirect(next)

    f_order_id = request.session['fOrderId']

    # get book id
    book_id = request.POST.get('book_id')

    # check to see if book already exists in future order
    future_book_exists = FutureOrderItem.objects.filter(future_order_id=f_order_id, book_id=book_id)

    # if book already exists in future order don't add again, display error message
    if future_book_exists:
        book = get_object_or_404(Book, id=book_id)
        messages.error(request, book.title + ' was already added to future order.')
    else:
        add_future_book = FutureOrderItem.objects.create(book_id=book_id, future_order_id=f_order_id)
        add_future_book.save()

        messages.success(request, add_future_book.book.title + ' was successfully added to future order.')

    return HttpResponseRedirect(next)


def remove_future_order_item(request, book_id):

    f_order_id = request.session['fOrderId']

    # get future book order item and the delete from database
    book_to_delete = get_object_or_404(FutureOrderItem, future_order_id=f_order_id, book_id=book_id)

    messages.success(request, book_to_delete.book.title + ' was successfully removed from future order.')

    book_to_delete.delete()

    return HttpResponseRedirect(reverse('payments:shoppingCart'))


def move_to_shopping_cart(request, book_id):

    f_order_id = request.session['fOrderId']

    book = get_object_or_404(Book, pk=book_id)

    # get user shopping cart id
    order_id = request.session['orderId']

    # get future book order item and the delete from database
    book_to_delete = get_object_or_404(FutureOrderItem, future_order_id=f_order_id, book_id=book_id)
    book_to_delete.delete()

    # check if book has already been added to shopping cart
    try:
        book_order_exists = OrderItem.objects.get(order_id=order_id, book_id=book_id)
        book_order_exists.quantity += 1
        book_order_exists.book_price_quantity += decimal.Decimal(book.price)
        book_order_exists.save()

    except OrderItem.DoesNotExist:

        # add book to shopping cart
        add_book = OrderItem.objects.create(quantity=1, book_id=book_id, order_id=order_id, book_price_quantity=book.price)
        add_book.save()

    # update order price, tax price, and total price
    update_cart_price(order_id, book.price)

    messages.success(request, book.title + ' was successfully moved to shopping cart.')

    return HttpResponseRedirect(reverse('payments:shoppingCart'))

#########################################################################################################
##                                   PAYMENT FUNCTIONS                                                 ##
########################################################################################################


def order_submit(request):
    user_id = request.user.user_id

    return render(request, 'payments/cartPurchased.html')