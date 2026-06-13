from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from . import views
from ramaqs_management_plateforme.views import LoginView
from .views import ChefProjetConsultantsView, CurrentUserView, ForgotPasswordView, RegisterView, UtilisateurDetailView, ValidateResetTokenView, ResetPasswordView,RegisterView ,NotificationViewSet  # ← Ajoute cet import
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from .views import TacheListCreateView, TacheDetailView
from rest_framework_simplejwt.views import TokenRefreshView
from .views import ConsultantListAPIView, ConsultantDetailAPIView

router = DefaultRouter()
router.register('projets', views.ProjetViewSet)
router.register('taches', views.TacheViewSet)
router.register('consultants', views.ConsultantViewSet)
router.register('clients', views.ClientViewSet)
router.register('chefProjets', views.ChefProjetViewSet)
router.register('directions', views.DirectionViewSet)
router.register('partenaires', views.PartenaireViewSet)
router.register('ressources', views.RessourceViewSet)
router.register('sousTaches', views.SousTacheViewSet)
router.register('documents', views.DocumentViewSet)
router.register('commentaires', views.CommentaireViewSet)
router.register('conversations', views.ConversationViewSet)
router.register('messages', views.MessageViewSet)
router.register('kpis', views.KpiViewSet)
router.register('budgets', views.BudgetViewSet)
router.register('utilisateurs', views.UtilisateurViewSet, basename='utilisateur')
router.register('notifications', NotificationViewSet, basename='notification')

urlpatterns = [
    path('api/', include(router.urls)),
    path('', include(router.urls)),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('auth/validate-reset-token/', ValidateResetTokenView.as_view(), name='validate-reset-token'),
    path('auth/reset-password/', ResetPasswordView.as_view(), name='reset-password'),
    path('projets/<uuid:projet_id>/consultants/', ChefProjetConsultantsView.as_view(), name='projet-consultants'),
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/me/', CurrentUserView.as_view(), name='current-user'),
    path('api/utilisateurs/<uuid:pk>/', UtilisateurDetailView.as_view(), name='utilisateur-detail'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # ✅ AJOUTE CES LIGNES POUR LES NOTIFICATIONS
    path('notifications/<uuid:pk>/lire/', NotificationViewSet.as_view({'patch': 'lire'}), name='notification-mark-read'),
    path('notifications/lire-tout/', NotificationViewSet.as_view({'patch': 'lire_tout'}), name='notification-mark-all-read'),
    # urls.py
    path('api/consultants/', ConsultantListAPIView.as_view(), name='consultant-list'),
    path('api/consultants/<uuid:pk>/', ConsultantDetailAPIView.as_view(), name='consultant-detail'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)