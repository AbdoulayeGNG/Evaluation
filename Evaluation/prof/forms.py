from django import forms
from utilisateurs.models import Professeur

class ProfesseurProfileForm(forms.ModelForm):
    class Meta:
        model = Professeur
        fields = ['departement', 'specialite', 'photo']
        widgets = {
            'departement': forms.TextInput(attrs={'class': 'form-control'}),
            'specialite': forms.TextInput(attrs={'class': 'form-control'}),
            'photo': forms.FileInput(attrs={'class': 'form-control-file'}),
        }