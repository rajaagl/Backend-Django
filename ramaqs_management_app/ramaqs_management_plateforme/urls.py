from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('projets', views.ProjetViewSet)
router.register('taches', views.TacheViewSet)
router.register('consultants', views.ConsultantViewSet)
router.register('clients', views.ClientViewSet)
router.register('chefProjets', views.chefProjetViewSet)
router.register('directions', views.directionViewSet)
router.register('partenaires', views.partenaireViewSet)
router.register('ressources', views.ressourceViewSet)
router.register('sousTaches', views.sousTacheViewSet)
router.register('documents', views.documentViewSet)
router.register('commentaires', views.commentaireViewSet)
router.register('notifications', views.notificationViewSet)
router.register('conversations', views.conversationViewSet)
router.register('messages', views.messageViewSet)
router.register('kpis', views.kpiViewSet)
router.register('budgets', views.budgetViewSet)

urlpatterns = [
    path('', include(router.urls)),
]