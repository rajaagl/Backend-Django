from django.shortcuts import render


from rest_framework import viewsets
from .models import projet, tache, consultant, client , chefProjet,partenaire,direction,ressource,sousTache,document,commentaire,notification,conversation,kpi,message,budget
from .serializers import (
    ProjetSerializer, TacheSerializer, 
    ConsultantSerializer, ClientSerializer,
    chefProjetSerializer,messageSerializer,
    budgetSerializer,conversationSerializer,
    commentaireSerializer,directionSerializer,
    documentSerializer, notificationSerializer,
    partenaireSerializer, ressourceSerializer
    ,sousTacheSerializer,kpiSerializer

)
# Create your views here.
class ProjetViewSet(viewsets.ModelViewSet):
    queryset = projet.objects.all()
    serializer_class = ProjetSerializer

class TacheViewSet(viewsets.ModelViewSet):
    queryset = tache.objects.all()
    serializer_class = TacheSerializer

class ConsultantViewSet(viewsets.ModelViewSet):
    queryset = consultant.objects.all()
    serializer_class = ConsultantSerializer

class ClientViewSet(viewsets.ModelViewSet):
    queryset = client.objects.all()
    serializer_class = ClientSerializer

class chefProjetViewSet(viewsets.ModelViewSet):
    queryset = chefProjet.objects.all()
    serializer_class = chefProjetSerializer

class directionViewSet(viewsets.ModelViewSet):
    queryset = direction.objects.all()
    serializer_class = directionSerializer

class partenaireViewSet(viewsets.ModelViewSet):
    queryset = partenaire.objects.all()
    serializer_class = partenaireSerializer

class ressourceViewSet(viewsets.ModelViewSet):
    queryset = ressource.objects.all()
    serializer_class = ressourceSerializer

class sousTacheViewSet(viewsets.ModelViewSet):
    queryset = sousTache.objects.all()
    serializer_class = sousTacheSerializer

class documentViewSet(viewsets.ModelViewSet):
    queryset = document.objects.all()
    serializer_class = documentSerializer

class commentaireViewSet(viewsets.ModelViewSet):
    queryset = commentaire.objects.all()
    serializer_class = commentaireSerializer

class notificationViewSet(viewsets.ModelViewSet):
    queryset = notification.objects.all()
    serializer_class = notificationSerializer   

class conversationViewSet(viewsets.ModelViewSet):
    queryset = conversation.objects.all()
    serializer_class = conversationSerializer

class messageViewSet(viewsets.ModelViewSet):
    queryset = message.objects.all()
    serializer_class = messageSerializer

class kpiViewSet(viewsets.ModelViewSet):
    queryset = kpi.objects.all()
    serializer_class = kpiSerializer

class budgetViewSet(viewsets.ModelViewSet):
    queryset = budget.objects.all()
    serializer_class = budgetSerializer

