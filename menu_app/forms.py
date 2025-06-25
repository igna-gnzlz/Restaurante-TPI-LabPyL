from django import forms

class AddOneForm(forms.Form):
    item_id = forms.IntegerField(widget=forms.HiddenInput())

class RemoveOneForm(forms.Form):
    item_id = forms.IntegerField(widget=forms.HiddenInput())

class DeleteItemForm(forms.Form):
    item_id = forms.IntegerField(widget=forms.HiddenInput())

class CancelOrderForm(forms.Form):
    order_id = forms.IntegerField(widget=forms.HiddenInput())
