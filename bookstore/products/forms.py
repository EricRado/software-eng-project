from django import forms
from .models import Review, Comment

CHOICES = [('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5')]


class ReviewForm(forms.ModelForm):
    user_rating = forms.ChoiceField(choices=CHOICES, widget=forms.RadioSelect(), label='Book Rating', required=True)
    review_header = forms.CharField(widget=forms.TextInput(attrs={'size': '20'}), label='Review Heading', required=True)
    review_body = forms.CharField(widget=forms.Textarea(attrs={'size': '10'}), label='Review Body', required=True)
    anonymous = forms.BooleanField(label='Anonymous', required=False)

    class Meta:
        model = Review
        fields = ['user_rating', 'review_header', 'review_body', 'anonymous']


class CommentForm(forms.ModelForm):
	book_id = forms.CharField(widget=forms.HiddenInput())
	user = forms.CharField(label="user", max_length=512)
	comment = forms.CharField(label="comment", max_length=4095)

	class Meta:
		model = Comment
		fields = ('book_id', 'comment', 'user')
