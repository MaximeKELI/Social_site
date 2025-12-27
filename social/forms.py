from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import School, Student, Post, Comment, Message


class SchoolRegistrationForm(UserCreationForm):
    """Formulaire d'inscription pour les écoles"""
    name = forms.CharField(max_length=200, label="Nom de l'école", widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(label="Email", widget=forms.EmailInput(attrs={'class': 'form-control'}))
    address = forms.CharField(label="Adresse", widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}))
    phone = forms.CharField(max_length=20, label="Téléphone", widget=forms.TextInput(attrs={'class': 'form-control'}))
    description = forms.CharField(required=False, label="Description", widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4}))
    logo = forms.ImageField(required=False, label="Logo", widget=forms.FileInput(attrs={'class': 'form-control'}))
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'name', 'address', 'phone', 'description', 'logo')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            school = School.objects.create(
                user=user,
                name=self.cleaned_data['name'],
                email=self.cleaned_data['email'],
                address=self.cleaned_data['address'],
                phone=self.cleaned_data['phone'],
                description=self.cleaned_data['description'],
            )
            if self.cleaned_data.get('logo'):
                school.logo = self.cleaned_data['logo']
                school.save()
        return user


class StudentRegistrationForm(UserCreationForm):
    """Formulaire d'inscription pour les étudiants"""
    first_name = forms.CharField(max_length=100, label="Prénom", widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=100, label="Nom", widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(label="Email", widget=forms.EmailInput(attrs={'class': 'form-control'}))
    phone = forms.CharField(max_length=20, required=False, label="Téléphone", widget=forms.TextInput(attrs={'class': 'form-control'}))
    graduation_year = forms.IntegerField(required=False, label="Année de diplôme", widget=forms.NumberInput(attrs={'class': 'form-control'}))
    status = forms.ChoiceField(choices=Student.GRADUATION_STATUS, label="Statut", widget=forms.Select(attrs={'class': 'form-control'}))
    bio = forms.CharField(required=False, label="Biographie", widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4}))
    profile_picture = forms.ImageField(required=False, label="Photo de profil", widget=forms.FileInput(attrs={'class': 'form-control'}))
    school = forms.ModelChoiceField(queryset=School.objects.filter(is_active=True), label="École", widget=forms.Select(attrs={'class': 'form-control'}))
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'first_name', 'last_name', 'phone', 'graduation_year', 'status', 'bio', 'profile_picture', 'school')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            student = Student.objects.create(
                user=user,
                school=self.cleaned_data['school'],
                first_name=self.cleaned_data['first_name'],
                last_name=self.cleaned_data['last_name'],
                email=self.cleaned_data['email'],
                phone=self.cleaned_data.get('phone', ''),
                graduation_year=self.cleaned_data.get('graduation_year'),
                status=self.cleaned_data['status'],
                bio=self.cleaned_data.get('bio', ''),
            )
            if self.cleaned_data.get('profile_picture'):
                student.profile_picture = self.cleaned_data['profile_picture']
                student.save()
        return user


class PostForm(forms.ModelForm):
    """Formulaire pour créer un post"""
    class Meta:
        model = Post
        fields = ('title', 'content', 'image')
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Titre du post'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Quoi de neuf ?'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'title': 'Titre',
            'content': 'Contenu',
            'image': 'Image',
        }


class CommentForm(forms.ModelForm):
    """Formulaire pour créer un commentaire"""
    class Meta:
        model = Comment
        fields = ('content',)
        widgets = {
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Ajouter un commentaire...'}),
        }
        labels = {
            'content': '',
        }


class MessageForm(forms.ModelForm):
    """Formulaire pour envoyer un message"""
    class Meta:
        model = Message
        fields = ('content',)
        widgets = {
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Tapez votre message...'}),
        }
        labels = {
            'content': '',
        }


