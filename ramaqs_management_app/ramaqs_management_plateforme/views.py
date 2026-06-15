from urllib import request

from django.shortcuts import render


from .permissions import IsTenantAuthenticated, IsTenantMember, IsTenantAdmin
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets, generics
from rest_framework.decorators import action
from rest_framework.response import Response
import logging
logger = logging.getLogger(__name__)
from .models import (
    Projet, RoleChoices, Tache, Consultant, Client, ChefProjet, 
    Partenaire, Direction, Ressource, SousTache, 
    Document, Commentaire, Notification, Conversation, 
    Kpi, Message, Budget, TenantMembership,
    Direction, ChefProjet, Consultant, Client, Partenaire, 
    Tenant, RoleChoices
)
from .serializers import (
    ProjetSerializer, TacheSerializer, 
    ConsultantSerializer, ClientSerializer,
    MessageSerializer,
    BudgetSerializer, ConversationSerializer,
    CommentaireSerializer, DirectionSerializer,
    DocumentSerializer, NotificationSerializer,
    PartenaireSerializer, RessourceSerializer,
    SousTacheSerializer, KpiSerializer,
    DirectionSerializer, ChefProjetSerializer, ConsultantSerializer, ClientSerializer, PartenaireSerializer, UtilisateurSerializer

)

from .permissions import IsTenantAuthenticated, IsTenantMember, IsTenantAdmin
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import secrets
from datetime import timedelta
from .models import Utilisateur, PasswordResetToken
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from rest_framework.permissions import AllowAny 
from django_filters.rest_framework import DjangoFilterBackend  # ← AJOUTER
from rest_framework import filters
from django.db import models  # ← AJOUTER CET IMPORT




# ========== VIEWSETS AVEC FILTRAGE TENANT ==========

class BaseTenantViewSet(viewsets.ModelViewSet):
    """
    ViewSet de base qui filtre automatiquement par tenant
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return self.queryset.all()
    
    def perform_create(self, serializer):
        """Assigne automatiquement le tenant à la création"""
        serializer.save(tenant=self.request.tenant)


class ProjetViewSet(BaseTenantViewSet):
    queryset = Projet.objects.all()
    serializer_class = ProjetSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    # Filtres exacts
    filterset_fields = {
        'statut': ['exact'],
        'priorite': ['exact'],
        'domaine': ['exact'],
        'avancement_globale': ['gte', 'lte'],
        'date_debut': ['gte', 'lte'],
        'date_fin_prevue': ['gte', 'lte'],
    }
    
    # Recherche texte
    search_fields = ['nom', 'description', 'code', 'client__nom']
    
    # Tri
    ordering_fields = ['nom', 'date_debut', 'date_fin_prevue', 'avancement_globale', 'budget']
    ordering = ['-date_debut']

    def get_queryset(self):
        user = self.request.user
        tenant = self.request.tenant
        # Filtrer par tenant
        queryset = Projet.objects.filter(tenant=tenant)
        
        # Récupérer le rôle de l'utilisateur
        role = user.get_role_in_tenant(tenant) if hasattr(user, 'get_role_in_tenant') else None
        
        if role == 'direction':
            # Direction voit tous les projets
            return queryset
        elif role == 'chef_projet':
            # Chef projet voit ses projets
            return queryset.filter(chef_projet=user)
        elif role == 'partenaire':
            # Partenaire voit uniquement les projets où il est partenaire
            return queryset.filter(partenaires=user)
        elif role == 'consultant':
            # Consultant voit les projets de ses tâches
            return queryset.filter(taches__consultant=user).distinct()
        else:
            return queryset.none()



class TacheViewSet(BaseTenantViewSet):
    queryset = Tache.objects.all()
    serializer_class = TacheSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    filterset_fields = {
        'statut': ['exact'],
        'priorite': ['exact'],
        'avancement': ['gte', 'lte'],
        'date_fin_prevue': ['gte', 'lte', 'exact'],
        'consultant': ['exact'],
        'projet': ['exact'],
    }
    
    search_fields = ['titre', 'description']
    ordering_fields = ['date_fin_prevue', 'avancement', 'priorite']

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def get_queryset(self):
        user = self.request.user
        tenant = self.request.tenant
        
        queryset = Tache.objects.filter(tenant=tenant)
        role = user.get_role_in_tenant(tenant) if hasattr(user, 'get_role_in_tenant') else None
        
        if role == 'direction':
            return queryset
        elif role == 'chef_projet':
            return queryset.filter(projet__chef_projet=user)
        elif role == 'partenaire':
            return queryset.filter(projet__partenaires=user)
        elif role == 'consultant':
            return queryset.filter(consultant=user)
        else:
            return queryset.none()
    
    def perform_destroy(self, instance):
        """Supprimer la tâche"""
        logger.info(f"Suppression de la tâche {instance.id} - {instance.titre}")
        
        # Vérification supplémentaire des permissions (optionnel)
        user = self.request.user
        tenant = self.request.tenant
        role = user.get_role_in_tenant(tenant) if hasattr(user, 'get_role_in_tenant') else None
        
        # Seuls direction et chef_projet peuvent supprimer
        if role not in ['direction', 'chef_projet']:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Vous n'avez pas la permission de supprimer cette tâche")
        
        # Suppression réelle
        instance.delete()
        logger.info(f"Tâche {instance.id} supprimée avec succès")
    def update(self, request, *args, **kwargs):
        """Contrôle des permissions pour la mise à jour (drag & drop)"""
        user = request.user
        tenant = request.tenant
        role = user.get_role_in_tenant(tenant) if hasattr(user, 'get_role_in_tenant') else None
        
        # Vérifications pour consultant
        if role == 'consultant':
            from rest_framework.exceptions import PermissionDenied
            instance = self.get_object()
            
            # Vérifier que la tâche appartient au consultant
            if instance.consultant != user:
                raise PermissionDenied("Vous ne pouvez modifier que vos propres tâches")
            
            # Champs autorisés pour le drag & drop
            allowed_fields = ['statut', 'avancement']
            
            # Vérifier que seuls les champs autorisés sont modifiés
            for field in request.data.keys():
                if field not in allowed_fields:
                    raise PermissionDenied(
                        f"Les consultants ne peuvent modifier que: {', '.join(allowed_fields)}"
                    )
        
        # Appeler la méthode update parente
        return super().update(request, *args, **kwargs)

    # Optionnel : Ajouter une méthode destroy personnalisée pour plus de contrôle
    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.error(f"Erreur lors de la suppression: {str(e)}")
            return Response(
                {'error': f'Erreur lors de la suppression: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

class ConsultantViewSet(BaseTenantViewSet):
    queryset = Consultant.objects.all()
    serializer_class = ConsultantSerializer


class ClientViewSet(BaseTenantViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer


class ChefProjetViewSet(BaseTenantViewSet):
    queryset = ChefProjet.objects.all()
    serializer_class = ChefProjetSerializer


class DirectionViewSet(BaseTenantViewSet):
    queryset = Direction.objects.all()
    serializer_class = DirectionSerializer


class PartenaireViewSet(BaseTenantViewSet):
    queryset = Partenaire.objects.all()
    serializer_class = PartenaireSerializer


class RessourceViewSet(BaseTenantViewSet):
    queryset = Ressource.objects.all()
    serializer_class = RessourceSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    # 🔽 FILTRES
    filterset_fields = {
        'type': ['exact'],
        'disponible': ['exact'],
        'cout_unitaire': ['gte', 'lte'],
        'projet': ['exact'],  # ← Filtre par projet
    }
    
    # 🔍 RECHERCHE
    search_fields = ['nom', 'type']
    
    # 📊 TRI
    ordering_fields = ['nom',  'cout_unitaire', 'disponible']
    def get_queryset(self):
         return Ressource.objects.all()
        

        


class SousTacheViewSet(BaseTenantViewSet):
    queryset = SousTache.objects.all()
    serializer_class = SousTacheSerializer
    
#--------------------------------------doc----------------------------------------------------------

# views.py
class DocumentViewSet(BaseTenantViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    @action(detail=True, methods=['post'])
    def commenter(self, request, pk=None):
        """Ajouter un commentaire à un document"""
        document = self.get_object()
        commentaire = request.data.get('commentaire')
        rating = request.data.get('rating')
        
        if not commentaire:
            return Response({'error': 'Commentaire requis'}, status=400)
        
        serializer = self.get_serializer()
        serializer.ajouter_commentaire(document, request.user, commentaire, rating)
        
        return Response({'status': 'ok'})


class CommentaireViewSet(BaseTenantViewSet):
    queryset = Commentaire.objects.all()
    serializer_class = CommentaireSerializer


class NotificationViewSet(BaseTenantViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer 
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        tenant = self.request.tenant
        role = user.get_role_in_tenant(tenant) if hasattr(user, 'get_role_in_tenant') else None
        
        # Base: notifications de l'utilisateur
        queryset = Notification.objects.filter(tenant=tenant, utilisateur=user)
        
        # ✅ Filtrer par rôle
        if role == 'direction':
            # Direction voit toutes les notifications du tenant
            return Notification.objects.filter(tenant=tenant)
            
        elif role == 'chef_projet':
            # Chef projet voit ses notifications + celles liées à ses projets
            projets_ids = Projet.objects.filter(chef_projet=user).values_list('id', flat=True)
            return Notification.objects.filter(
                models.Q(utilisateur=user) |
                models.Q(projet__id__in=projets_ids)
            ).distinct()
            
        else:
            # Consultant/client voit uniquement ses propres notifications
            return queryset   
    @action(detail=True, methods=['patch'], url_path='lire')
    def mark_as_read(self, request, pk=None):
        """Marquer une notification comme lue"""
        notification = self.get_object()
        notification.lue = True
        notification.save()
        return Response({'status': 'ok', 'lue': True})
    
    @action(detail=False, methods=['patch'], url_path='lire-tout')
    def mark_all_as_read(self, request):
        """Marquer toutes les notifications comme lues"""
        notifications = self.get_queryset().filter(lue=False)
        count = notifications.count()
        notifications.update(lue=True)
        return Response({'status': 'ok', 'count': count})


class ConversationViewSet(BaseTenantViewSet):
    queryset = Conversation.objects.all()
    serializer_class = ConversationSerializer


class MessageViewSet(BaseTenantViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer


class KpiViewSet(BaseTenantViewSet):
    queryset = Kpi.objects.all()
    serializer_class = KpiSerializer


class BudgetViewSet(BaseTenantViewSet):
    queryset = Budget.objects.all()
    serializer_class = BudgetSerializer

class DirectionViewSet(BaseTenantViewSet):
    queryset = Direction.objects.all()
    serializer_class = DirectionSerializer  # À créer

class ChefProjetViewSet(BaseTenantViewSet):
    queryset = ChefProjet.objects.all()
    serializer_class = ChefProjetSerializer  # À créer

# views.py
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import Utilisateur
from .serializers import ConsultantSerializer

class ConsultantListAPIView(generics.ListAPIView):
    serializer_class = ConsultantSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        tenant = self.request.tenant
        return Utilisateur.objects.filter(
            role='consultant',
            memberships__tenant=tenant,
            is_active=True
        ).order_by('nom')


class ConsultantDetailAPIView(generics.RetrieveAPIView):
    serializer_class = ConsultantSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'pk'
    
    def get_queryset(self):
        tenant = self.request.tenant
        return Utilisateur.objects.filter(
            role='consultant',
            memberships__tenant=tenant,
            is_active=True
        )

class ClientViewSet(BaseTenantViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer  # À créer

class PartenaireViewSet(BaseTenantViewSet):
    queryset = Partenaire.objects.all()
    serializer_class = PartenaireSerializer  # À créer


class ProjetListCreateView(generics.ListCreateAPIView):
    serializer_class = ProjetSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        tenant = self.request.tenant
        return Projet.objects.filter(tenant=tenant)
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


# ========== INSCRIPTION ==========

class RegisterView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []  
    
    def post(self, request):
        print("Données reçues:", request.data)  # ← AJOUTEZ CE LOG
        email = request.data.get('email')
        nom = request.data.get('nom')
        password = request.data.get('password')
        role = request.data.get('role', 'consultant')
        telephone = request.data.get('telephone', '')
        entreprise = request.data.get('entreprise', '')
        poste = request.data.get('poste', '')
        
        # Vérifier si l'utilisateur existe déjà
        if Utilisateur.objects.filter(email=email).exists():
            return Response(
                {'error': 'Un compte existe déjà avec cet email'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Créer l'utilisateur
        user = Utilisateur.objects.create_user(
            username=email,
            email=email,
            password=password,
            nom=nom,
            telephone=telephone
        )
        
        # Ajouter les champs supplémentaires
        if entreprise:
            user.entreprise = entreprise
        if poste:
            user.poste = poste
        user.save()
        
        # Assigner au tenant par défaut
        tenant = Tenant.objects.first()
        if tenant:
            role_map = {
                'direction': RoleChoices.DIRECTION,
                'chef_projet': RoleChoices.CHEF_PROJET,
                'consultant': RoleChoices.CONSULTANT,
                'client': RoleChoices.CLIENT,
                'partenaire': RoleChoices.PARTENAIRE,
            }
            role_choice = role_map.get(role, RoleChoices.CONSULTANT)
            
            TenantMembership.objects.create(
                user=user,
                tenant=tenant,
                role=role_choice
            )
        
        return Response({
            'message': 'Utilisateur créé avec succès',
            'user': {
                'id': str(user.id),
                'email': user.email,
                'nom': user.nom,
                'role': role
            }
        }, status=status.HTTP_201_CREATED)


class LoginView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    
    
# ========== MOT DE PASSE OUBLIÉ ==========

class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        
        if not email:
            return Response({'error': 'Email requis'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = Utilisateur.objects.get(email=email)
        except Utilisateur.DoesNotExist:
            # Sécurité : ne pas révéler si l'email existe
            return Response({
                'message': 'Si un compte existe, vous recevrez un email.'
            }, status=status.HTTP_200_OK)
        
        # Supprimer les anciens tokens expirés
        PasswordResetToken.objects.filter(user=user, used=False, expires_at__lt=timezone.now()).delete()
        
        # Créer un nouveau token
        token = secrets.token_urlsafe(32)
        expires_at = timezone.now() + timedelta(hours=24)
        
        reset_token = PasswordResetToken.objects.create(
            user=user,
            token=token,
            expires_at=expires_at
        )
        
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        reset_link = f"{frontend_url}/reset-password?token={token}"
        
        # Pour le développement : afficher le lien dans la console
        print(f"\n{'='*50}")
        print(f"🔐 LIEN DE RÉINITIALISATION POUR {user.email}")
        print(f"🔗 {reset_link}")
        print(f"📝 Token: {token}")
        print(f"⏰ Expire dans 24 heures")
        print(f"{'='*50}\n")
        
        # Optionnel : envoyer un vrai email (à configurer plus tard)
        # try:
        #     send_mail(
        #         subject='Réinitialisation de votre mot de passe',
        #         message=f'Cliquez sur ce lien pour réinitialiser votre mot de passe: {reset_link}',
        #         from_email=settings.DEFAULT_FROM_EMAIL,
        #         recipient_list=[user.email],
        #         fail_silently=False,
        #     )
        # except Exception as e:
        #     print(f"Erreur d'envoi d'email: {e}")
        
        return Response({
            'message': 'Email envoyé avec succès',
            'reset_link': reset_link  # Pour le développement uniquement
        }, status=status.HTTP_200_OK)


class ValidateResetTokenView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        token = request.data.get('token')
        
        if not token:
            return Response({'valid': False, 'error': 'Token requis'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            reset_token = PasswordResetToken.objects.get(token=token, used=False)
        except PasswordResetToken.DoesNotExist:
            return Response({'valid': False, 'error': 'Token invalide'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not reset_token.is_valid():
            return Response({'valid': False, 'error': 'Token expiré'}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'valid': True,
            'email': reset_token.user.email
        }, status=status.HTTP_200_OK)


class ResetPasswordView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        token = request.data.get('token')
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')
        
        if not token or not new_password or not confirm_password:
            return Response({
                'error': 'Tous les champs sont requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if new_password != confirm_password:
            return Response({
                'error': 'Les mots de passe ne correspondent pas'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if len(new_password) < 6:
            return Response({
                'error': 'Le mot de passe doit contenir au moins 6 caractères'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            reset_token = PasswordResetToken.objects.get(token=token, used=False)
        except PasswordResetToken.DoesNotExist:
            return Response({
                'error': 'Token invalide'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not reset_token.is_valid():
            return Response({
                'error': 'Token expiré'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Réinitialiser le mot de passe
        user = reset_token.user
        user.set_password(new_password)
        user.save()
        
        # Marquer le token comme utilisé
        reset_token.used = True
        reset_token.save()
        
        # Supprimer tous les autres tokens de cet utilisateur
        PasswordResetToken.objects.filter(user=user).exclude(id=reset_token.id).delete()
        
        return Response({
            'message': 'Mot de passe réinitialisé avec succès'
        }, status=status.HTTP_200_OK)
    



class ChefProjetConsultantsView(APIView):
    """Récupère tous les consultants d'un chef de projet pour un projet donné"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, projet_id):
        user = request.user
        tenant = request.tenant
        
        # Vérifier que l'utilisateur est chef de projet sur ce projet
        try:
            projet = Projet.objects.get(id=projet_id, tenant=tenant)
        except Projet.DoesNotExist:
            return Response({'error': 'Projet non trouvé'}, status=404)
        
        # Vérifier les droits (chef projet ou direction)
        role = user.get_role_in_tenant(tenant)
        if role not in ['direction', 'chef_projet']:
            return Response({'error': 'Non autorisé'}, status=403)
        
        # Si chef projet, vérifier qu'il est bien le chef de ce projet
        if role == 'chef_projet' and projet.chef_projet != user:
            return Response({'error': 'Vous n\'êtes pas le chef de ce projet'}, status=403)
        
        # Récupérer tous les consultants du projet (via les tâches)
        consultants = Utilisateur.objects.filter(
            taches__projet=projet,
            role='consultant'
        ).distinct()
        
        # Formatage des données
        data = []
        for consultant in consultants:
            # Récupérer les tâches du consultant sur ce projet
            taches = Tache.objects.filter(consultant=consultant, projet=projet)
            
            data.append({
                'id': str(consultant.id),
                'nom': consultant.nom,
                'email': consultant.email,
                'telephone': consultant.telephone,
                'photo_profil': consultant.photo_profil.url if consultant.photo_profil else None,
                'competences': consultant.competences,
                'taches': [
                    {
                        'id': str(tache.id),
                        'titre': tache.titre,
                        'avancement': tache.avancement,
                        'statut': tache.statut
                    } for tache in taches
                ],
                'total_taches': taches.count(),
                'avancement_moyen': sum(t.avancement for t in taches) / taches.count() if taches else 0
            })
        
        return Response({
            'projet': {
                'id': str(projet.id),
                'nom': projet.nom,
                'chef_projet': {
                    'id': str(projet.chef_projet.id),
                    'nom': projet.chef_projet.nom,
                    'email': projet.chef_projet.email
                }
            },
            'consultants': data,
            'total_consultants': len(data)
        })
    
# views/auth_views.py
class CurrentUserView(APIView):
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user

        photo_url = None
        if user.photo_profil and user.photo_profil.name:
            try:
                # Retourner l'URL complète
                photo_url = request.build_absolute_uri(user.photo_profil.url)
            except:
                photo_url = None
        
        # Récupérer le rôle dans le tenant
        role = user.get_role_in_tenant(request.tenant) if hasattr(user, 'get_role_in_tenant') else user.role
        
        return Response({
            'id': str(user.id),
            'nom': user.nom,
            'email': user.email,
            'telephone': user.telephone or None,
            'poste': user.poste or None,
            'departement': None,  # Votre modèle n'a pas de champ 'departement'
            'entreprise': user.entreprise or None,
            'dateEntree': user.date_creation,
            'photo_profil': photo_url,
            'role': role,
        })

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh_token')
            if refresh_token:
                from rest_framework_simplejwt.tokens import RefreshToken
                token = RefreshToken(refresh_token)
                token.blacklist()
            return Response({'message': 'Déconnecté avec succès'})
        except Exception:
            return Response({'message': 'Déconnecté'})
        
class UtilisateurDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UtilisateurSerializer
    
    def get_queryset(self):
        # L'utilisateur ne peut voir/modifier que son propre profil
        return Utilisateur.objects.filter(id=self.request.user.id)
    
    def get_object(self):
        # Retourne l'utilisateur connecté, indépendamment de l'ID dans l'URL
        return self.request.user
    
    def update(self, request, *args, **kwargs):
        user = self.request.user
        
        # Gérer spécialement l'upload de photo
        if 'photo_profil' in request.FILES:
            user.photo_profil = request.FILES['photo_profil']
        
        # Mettre à jour les autres champs
        for field in ['nom', 'telephone', 'poste', 'entreprise']:
            if field in request.data:
                setattr(user, field, request.data[field])
        
        user.save()
        
        return Response({
            'id': str(user.id),
            'nom': user.nom,
            'email': user.email,
            'telephone': user.telephone,
            'poste': user.poste,
            'entreprise': user.entreprise,
            'photo_profil': user.photo_profil.url if user.photo_profil else None,
            'role': user.get_role_in_tenant(request.tenant) if hasattr(user, 'get_role_in_tenant') else user.role,
        })
    

class UtilisateurViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = UtilisateurSerializer
    
    def get_queryset(self):
        # L'utilisateur ne peut voir que son propre profil
        return Utilisateur.objects.filter(id=self.request.user.id)
    
    def get_object(self):
        # Retourne l'utilisateur connecté
        return self.request.user
    
    def update(self, request, *args, **kwargs):
        user = self.request.user
        
        # Gérer l'upload de photo
        if 'photo_profil' in request.FILES:
            user.photo_profil = request.FILES['photo_profil']
        
        # Mettre à jour les champs texte
        updatable_fields = ['nom', 'telephone', 'poste', 'entreprise']
        for field in updatable_fields:
            if field in request.data and request.data[field]:
                setattr(user, field, request.data[field])
        
        user.save()
        
        # Construire la réponse
        photo_url = None
        if user.photo_profil:
            try:
                photo_url = user.photo_profil.url
            except:
                photo_url = None
        
        return Response({
            'id': str(user.id),
            'nom': user.nom,
            'email': user.email,
            'telephone': user.telephone,
            'poste': user.poste,
            'entreprise': user.entreprise,
            'photo_profil': photo_url,
            'role': user.get_role_in_tenant(request.tenant) if hasattr(user, 'get_role_in_tenant') else getattr(user, 'role', 'consultant'),
            'dateEntree': user.date_creation,
        })
    
# views.py
from rest_framework import generics
from rest_framework.response import Response
from .models import Tache

class TacheListCreateView(generics.ListCreateAPIView):
    queryset = Tache.objects.all()
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        
        data = []
        for task in queryset:
            data.append({
                'id': str(task.id),
                'title': task.titre,
                'description': task.description,
                'priority': task.priorite,
                'status': self.map_status(task.statut),
                'avancement': float(task.avancement),
                'dateEcheance': task.date_fin_prevue,
                'projetId': str(task.projet.id) if task.projet else None,
                'assigneA': str(task.consultant.id) if task.consultant else None,
                'assigneNom': task.consultant.nom if task.consultant else None,
            })
        
        return Response({
            'count': len(data),
            'results': data
        })
    
    def map_status(self, statut):
        mapping = {
            'en cours': 'en_cours',
            'termine': 'termine',
            'a_faire': 'a_faire'
        }
        return mapping.get(statut, 'a_faire')
    
class TacheDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TacheSerializer
    
    def get_queryset(self):
        tenant = self.request.tenant
        return Tache.objects.filter(tenant=tenant)
    
    def retrieve(self, request, *args, **kwargs):
        task = self.get_object()
        
        data = {
            'id': str(task.id),
            'title': task.titre,
            'description': task.description,
            'priority': task.priorite,
            'status': 'en_cours' if task.statut == 'en cours' else task.statut,
            'avancement': float(task.avancement),
            'dateEcheance': task.date_fin_prevue,
            'projetId': str(task.projet.id) if task.projet else None,
            'assigneA': str(task.consultant.id) if task.consultant else None,
            'assigneNom': task.consultant.nom if task.consultant else None,
        }
        
        return Response(data)