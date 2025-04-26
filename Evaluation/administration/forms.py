from django import forms
from django.contrib.auth.forms import UserCreationForm
from evaluationProf.models import Formation
from django.conf import settings
from utilisateurs.models import Utilisateur, Administrateur

class FormationForm(forms.ModelForm):
    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Description de la formation'
        })
    )
    
    class Meta:
        model = Formation
        fields = ['nom', 'description', 'professeur', 'niveau', 'departement', 'semestre']
        widgets = {
            'nom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom de la formation'
            }),
            'professeur': forms.Select(attrs={
                'class': 'form-control select2',
                'placeholder': 'Sélectionnez un professeur'
            }),
            'niveau': forms.Select(attrs={
                'class': 'form-control select2',
                'choices': Formation.NIVEAUX_CHOICES,
                'placeholder': 'Sélectionnez un niveau'
            }),
            'departement': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom du département'
            }),
            'semestre': forms.Select(attrs={
                'class': 'form-control select2',
                'placeholder': 'Sélectionnez un semestre'
            })
        }

    def clean(self):
        cleaned_data = super().clean()
        nom = cleaned_data.get('nom')
        semestre = cleaned_data.get('semestre')
        departement = cleaned_data.get('departement')
        niveau = cleaned_data.get('niveau')


        # Vérifier les doublons en excluant l'instance actuelle
        formations_existantes = Formation.objects.filter(
            nom=nom,
            semestre=semestre,
            departement=departement,
            niveau=niveau
        )
        
        # Si c'est une modification, exclure l'instance actuelle
        if self.instance.pk:
            formations_existantes = formations_existantes.exclude(pk=self.instance.pk)
        
        if formations_existantes.exists():
            raise forms.ValidationError(
                "Une formation avec ce nom existe déjà pour ce semestre et ce département."
            )
        
        return cleaned_data

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrer les professeurs pour n'afficher que ceux ayant le rôle 'professeur'
        self.fields['professeur'].queryset = self.fields['professeur'].queryset.filter(
            role='professeur'
        )
        # Rendre tous les champs obligatoires
        for field in self.fields:
            self.fields[field].required = True
            if self.fields[field].widget.attrs.get('class'):
                self.fields[field].widget.attrs['class'] += ' required'
            else:
                self.fields[field].widget.attrs['class'] = 'required'

class AdministrateurCreationForm(UserCreationForm):
    nom = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nom de l\'administrateur'
        })
    )
    prenom = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Prénom de l\'administrateur'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email'
        })
    )
    contact = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Numéro de téléphone'
        })
    )
    photo = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        })
    )

    class Meta(UserCreationForm.Meta):
        model = Utilisateur
        fields = ['username', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'admin'
        if commit:
            user.save()
            Administrateur.objects.create(
                user=user,
                nom=self.cleaned_data.get('nom'),
                prenom=self.cleaned_data.get('prenom'),
                contact=self.cleaned_data.get('contact'),
                photo=self.cleaned_data.get('photo')
            )
        return user

class AdministrateurForm(forms.ModelForm):
    username = forms.CharField(
        label="Nom d'utilisateur",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text='Laissez vide pour conserver le mot de passe actuel'
    )
    nom = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    prenom = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    contact = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    photo = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        })
    )
    password1 = forms.CharField(
        label='Nouveau mot de passe',
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Laissez vide pour conserver le mot de passe actuel'
        })
    )
    password2 = forms.CharField(
        label='Confirmer le mot de passe',
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirmez le nouveau mot de passe'
        })
    )

    class Meta:
        model = Administrateur
        fields = ['nom', 'prenom', 'contact', 'photo']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['username'].initial = self.instance.user.username
            self.fields['email'].initial = self.instance.user.email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if Utilisateur.objects.exclude(administrateur=self.instance).filter(username=username).exists():
            raise forms.ValidationError("Ce nom d'utilisateur est déjà pris.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Utilisateur.objects.exclude(administrateur=self.instance).filter(email=email).exists():
            raise forms.ValidationError("Cette adresse email est déjà utilisée.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1:
            if not password2:
                raise forms.ValidationError("Veuillez confirmer le mot de passe")
            if password1 != password2:
                raise forms.ValidationError("Les mots de passe ne correspondent pas")

        return cleaned_data

    def save(self, commit=True):
        administrateur = super().save(commit=False)
        if self.cleaned_data.get('password1'):
            administrateur.user.set_password(self.cleaned_data['password1'])
            administrateur.user.save()
        if commit:
            administrateur.save()
        return administrateur