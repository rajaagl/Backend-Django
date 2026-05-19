# ramaqs_management_plateforme/serializers.py
from rest_framework import serializers
from .models import projet, tache, consultant, client,chefProjet,partenaire,direction,ressource,sousTache,document,commentaire,notification,conversation,kpi, message,budget


class ProjetSerializer(serializers.ModelSerializer):
    class Meta:
        model = projet
        fields = '__all__'

class TacheSerializer(serializers.ModelSerializer):
    class Meta:
        model = tache
        fields = '__all__'

class ConsultantSerializer(serializers.ModelSerializer):
    class Meta:
        model = consultant
        fields = '__all__'

class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = client
        fields = '__all__'

class chefProjetSerializer(serializers.ModelSerializer):
    class Meta :
        model = chefProjet
        fields = '__all__'

class partenaireSerializer(serializers.ModelSerializer):
    class Meta :
        model = partenaire
        fields = '__all__'

class directionSerializer(serializers.ModelSerializer):
    class Meta :
        model = direction
        fields = '__all__'

class ressourceSerializer(serializers.ModelSerializer):
    class Meta :
        model = ressource
        fields = '__all__'

class sousTacheSerializer(serializers.ModelSerializer):
    class Meta :
        model = sousTache
        fields = '__all__'

class documentSerializer(serializers.ModelSerializer):  
    class Meta :
        model = document
        fields = '__all__'  

class conversationSerializer(serializers.ModelSerializer):
    class Meta :
        model = conversation
        fields = '__all__'

class commentaireSerializer(serializers.ModelSerializer):
    class Meta :
        model = commentaire
        fields = '__all__'

class notificationSerializer(serializers.ModelSerializer):
    class Meta :
        model = notification
        fields = '__all__'


class kpiSerializer(serializers.ModelSerializer):
    class Meta :
        model = kpi
        fields = '__all__'

class messageSerializer(serializers.ModelSerializer):
    class Meta :
        model = message
        fields = '__all__'

class budgetSerializer(serializers.ModelSerializer):
    class Meta :
        model = budget
        fields = '__all__'