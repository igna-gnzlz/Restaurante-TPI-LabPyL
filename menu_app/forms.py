from django import forms
from menu_app.models import Rating


class AddOneForm(forms.Form):
    item_id = forms.IntegerField(widget=forms.HiddenInput())


class RemoveOneForm(forms.Form):
    item_id = forms.IntegerField(widget=forms.HiddenInput())


class DeleteItemForm(forms.Form):
    item_id = forms.IntegerField(widget=forms.HiddenInput())


class CancelOrderForm(forms.Form):
    order_id = forms.IntegerField(widget=forms.HiddenInput())


class RatingForm(forms.ModelForm):
    class Meta:
        model = Rating
        fields = ['title', 'text', 'rating']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título del comentario'
            }),
            'text': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Escriba su comentario...',
                'rows': 3
            }),
            'rating': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 5,
                'placeholder': 'Calificación (1 a 5)'
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        title = cleaned_data.get('title')
        text = cleaned_data.get('text')
        rating = cleaned_data.get('rating')

        errors = Rating.validate(title, text, rating)

        if errors:
            for field, message in errors.items():
                self.add_error(field, message)
        return cleaned_data 

