from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Récupère la valeur d'un dictionnaire à partir de la clé"""
    return dictionary.get(key, "")
