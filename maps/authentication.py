import re
from django import forms
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User

# ==========================================
# 1. CUSTOM FORM REGISTER
# ==========================================
class CustomRegisterForm(forms.ModelForm):
    username = forms.CharField(max_length=150, required=True, label="Username")
    email = forms.EmailField(required=True, label="Email (Khusus @gmail.com)")
    password = forms.CharField(widget=forms.PasswordInput, label="Password")
    password_confirmation = forms.CharField(widget=forms.PasswordInput, label="Konfirmasi Password")

    class Meta:
        model = User
        fields = ['username', 'email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hapus semua "teks ganggu" (help_text) bawaan Django
        for field in self.fields.values():
            field.help_text = ''
            
    def clean_username(self):
        username = self.cleaned_data.get('username')
        # Cek apakah username sudah ada di database
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Username ini sudah dipakai. Silakan pilih nama lain.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        # Aturan: Wajib @gmail.com
        if not email.endswith('@gmail.com'):
            raise forms.ValidationError("Harus menggunakan email valid dari Google (@gmail.com).")
        # Aturan: Tidak boleh ada email ganda
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email ini sudah terdaftar.")
        return email

    def clean_password(self):
        password = self.cleaned_data.get('password')
        # Aturan: Minimal 8 karakter, 1 Huruf Besar, 1 Huruf Kecil, 1 Angka
        if len(password) < 8:
            raise forms.ValidationError("Password minimal 8 karakter.")
        if not re.search(r'[A-Z]', password):
            raise forms.ValidationError("Password harus mengandung minimal 1 huruf besar.")
        if not re.search(r'[a-z]', password):
            raise forms.ValidationError("Password harus mengandung minimal 1 huruf kecil.")
        if not re.search(r'[0-9]', password):
            raise forms.ValidationError("Password harus mengandung minimal 1 angka.")
        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirmation = cleaned_data.get("password_confirmation")

        # Aturan: Konfirmasi password harus sama
        if password and password_confirmation and password != password_confirmation:
            self.add_error('password_confirmation', "Konfirmasi password tidak cocok.")
        return cleaned_data

    def save(self, commit=True):
        # Enkripsi password sebelum disimpan ke database
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


# ==========================================
# 2. LOGIKA VIEWS AUTENTIKASI
# ==========================================
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard')
    else:
        form = AuthenticationForm()
        
    return render(request, 'maps/login.html', {'form': form})

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        # Pakai Custom Form yang baru dibuat
        form = CustomRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = CustomRegisterForm()
        
    return render(request, 'maps/register.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')