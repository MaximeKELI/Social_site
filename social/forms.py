from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.conf import settings
from .models import School, Student, Post, Comment, Message
from .security import validate_file_upload, sanitize_input


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
    
    def clean_name(self):
        """Valide et nettoie le nom de l'école"""
        name = self.cleaned_data.get('name')
        if name:
            name = sanitize_input(name, max_length=200)
        return name
    
    def clean_address(self):
        """Valide et nettoie l'adresse"""
        address = self.cleaned_data.get('address')
        if address:
            address = sanitize_input(address, max_length=500)
        return address
    
    def clean_description(self):
        """Valide et nettoie la description"""
        description = self.cleaned_data.get('description')
        if description:
            description = sanitize_input(description, max_length=1000)
        return description
    
    def clean_logo(self):
        """Valide le logo uploadé"""
        logo = self.cleaned_data.get('logo')
        if logo:
            is_valid, error = validate_file_upload(
                logo,
                allowed_types=getattr(settings, 'SECURITY_ALLOWED_IMAGE_TYPES', None),
                max_size=getattr(settings, 'SECURITY_MAX_FILE_SIZE', 5*1024*1024),
                is_image=True
            )
            if not is_valid:
                raise ValidationError(error)
        return logo
    
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
    
    def clean_first_name(self):
        """Valide et nettoie le prénom"""
        first_name = self.cleaned_data.get('first_name')
        if first_name:
            first_name = sanitize_input(first_name, max_length=100)
        return first_name
    
    def clean_last_name(self):
        """Valide et nettoie le nom"""
        last_name = self.cleaned_data.get('last_name')
        if last_name:
            last_name = sanitize_input(last_name, max_length=100)
        return last_name
    
    def clean_bio(self):
        """Valide et nettoie la biographie"""
        bio = self.cleaned_data.get('bio')
        if bio:
            bio = sanitize_input(bio, max_length=500)
        return bio
    
    def clean_profile_picture(self):
        """Valide la photo de profil uploadée"""
        profile_picture = self.cleaned_data.get('profile_picture')
        if profile_picture:
            is_valid, error = validate_file_upload(
                profile_picture,
                allowed_types=getattr(settings, 'SECURITY_ALLOWED_IMAGE_TYPES', None),
                max_size=getattr(settings, 'SECURITY_MAX_FILE_SIZE', 5*1024*1024),
                is_image=True
            )
            if not is_valid:
                raise ValidationError(error)
        return profile_picture
    
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
    
    def clean_title(self):
        """Valide et nettoie le titre"""
        title = self.cleaned_data.get('title')
        if title:
            title = sanitize_input(title, max_length=200)
        return title
    
    def clean_content(self):
        """Valide et nettoie le contenu"""
        content = self.cleaned_data.get('content')
        if content:
            content = sanitize_input(content, max_length=5000)
        return content
    
    def clean_image(self):
        """Valide l'image uploadée"""
        image = self.cleaned_data.get('image')
        if image:
            is_valid, error = validate_file_upload(
                image,
                allowed_types=getattr(settings, 'SECURITY_ALLOWED_IMAGE_TYPES', None),
                max_size=getattr(settings, 'SECURITY_MAX_FILE_SIZE', 5*1024*1024),
                is_image=True
            )
            if not is_valid:
                raise ValidationError(error)
        return image


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
    
    def clean_content(self):
        """Valide et nettoie le contenu du commentaire"""
        content = self.cleaned_data.get('content')
        if content:
            content = sanitize_input(content, max_length=1000)
        return content


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
    
    def clean_content(self):
        """Valide et nettoie le contenu du message"""
        content = self.cleaned_data.get('content')
        if content:
            content = sanitize_input(content, max_length=2000)
        return content


