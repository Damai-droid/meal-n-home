from django import forms
from .models import Order, Partnership


class OrderForm(forms.ModelForm):
    quantity = forms.IntegerField(min_value=1, max_value=20, initial=1, required=False)
    referral_code = forms.CharField(max_length=20, required=False,
                                    widget=forms.TextInput(attrs={'placeholder': 'Kode Referral (opsional)'}))

    class Meta:
        model = Order
        fields = ['customer_name', 'customer_email', 'customer_phone',
                  'customer_address', 'payment_method', 'notes']
        widgets = {
            'customer_name': forms.TextInput(attrs={'placeholder': 'Nama lengkap Anda'}),
            'customer_email': forms.EmailInput(attrs={'placeholder': 'email@contoh.com'}),
            'customer_phone': forms.TextInput(attrs={'placeholder': '08xxxxxxxxxx'}),
            'customer_address': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Alamat lengkap pengiriman'}),
            'notes': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Catatan khusus (opsional)'}),
        }


class PartnershipForm(forms.ModelForm):
    class Meta:
        model = Partnership
        fields = ['company_name', 'contact_person', 'email', 'phone', 'message']
        widgets = {
            'company_name': forms.TextInput(attrs={'placeholder': 'Nama perusahaan / instansi'}),
            'contact_person': forms.TextInput(attrs={'placeholder': 'Nama PIC / kontak person'}),
            'email': forms.EmailInput(attrs={'placeholder': 'email@perusahaan.com'}),
            'phone': forms.TextInput(attrs={'placeholder': '08xxxxxxxxxx'}),
            'message': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Jelaskan kebutuhan kerjasama Anda...'}),
        }