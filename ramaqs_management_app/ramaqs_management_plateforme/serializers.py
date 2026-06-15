from rest_framework import serializers
from .models import (
    Projet, Tache, SousTache, Document, Commentaire,
    Notification, Conversation, Message, Kpi, Budget,
    Ressource, Utilisateur, Tenant, TenantMembership,
    Direction, ChefProjet, Consultant, Client, Partenaire
)

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models import Avg
# serializers.py
from .services.notification_service import NotificationService
# serializers.py
from rest_framework import serializers
from .models import Document, Notification, Utilisateur, Projet
from .services.notification_service import NotificationService

# ========== UTILISATEUR & TENANT ==========

class UtilisateurSerializer(serializers.ModelSerializer):
    class Meta:
        model = Utilisateur
        fields = [
            'id', 
            'nom', 
            'email', 
            'telephone', 
            'photo_profil', 
            'date_creation', 
            'dernier_connexion', 
            'actif',
            # ✅ AJOUTER CES CHAMPS POUR L'APPROBATION
            'role',
            'statut_approbation',
            'justification_rejet',
            'date_approbation',
            'approuve_par',
            'is_active',
            'entreprise',
            'poste',
        ]
        read_only_fields = ['id', 'date_creation', 'dernier_connexion']

class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = ['id', 'nom', 'slug', 'secteur_activite', 'logo', 'date_creation', 'actif']
        read_only_fields = ['id', 'date_creation']


class TenantMembershipSerializer(serializers.ModelSerializer):
    user_email = serializers.ReadOnlyField(source='user.email')
    tenant_nom = serializers.ReadOnlyField(source='tenant.nom')
    
    class Meta:
        model = TenantMembership
        fields = ['id', 'user', 'user_email', 'tenant', 'tenant_nom', 'role', 'date_joined']
        read_only_fields = ['id', 'date_joined']


# ========== MODÈLES SPÉCIFIQUES (HÉRITENT DE UTILISATEUR) ==========

class DirectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Direction
        fields = ['id', 'nom', 'email', 'telephone', 'photo_profil', 
                   'date_creation', 'actif']
        read_only_fields = ['id', 'date_creation']


class ChefProjetSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChefProjet
        fields = ['id', 'nom', 'email', 'telephone', 'photo_profil',
                  'specialite', 'certifications', 'date_creation', 'actif']
        read_only_fields = ['id', 'date_creation']


# serializers.py
from rest_framework import serializers
from .models import Utilisateur, Tache

class ConsultantSerializer(serializers.ModelSerializer):
    chef_projet_nom = serializers.SerializerMethodField()
    nombre_taches = serializers.SerializerMethodField()
    avancement_moyen = serializers.SerializerMethodField()
    
    class Meta:
        model = Utilisateur
        fields = [
            'id', 
            'nom', 
            'email', 
            'telephone', 
            'photo_profil',
            'entreprise', 
            'poste',
            'role',
            'chef_projet_nom',
            'nombre_taches',
            'avancement_moyen',
            'date_creation', 
            'actif'
        ]
        read_only_fields = ['id', 'date_creation']
    
    def get_chef_projet_nom(self, obj):
        """Récupère le nom du chef de projet associé à ce consultant"""
        # Chercher une tâche où ce consultant est assigné
        tache = obj.taches.first()
        if tache and tache.projet and tache.projet.chef_projet:
            return tache.projet.chef_projet.nom
        return None
    
    def get_nombre_taches(self, obj):
        """Nombre total de tâches assignées à ce consultant"""
        return obj.taches.count()
    
    def get_avancement_moyen(self, obj):
        """Avancement moyen des tâches du consultant"""
        taches = obj.taches.all()
        if taches.exists():
            avg = taches.aggregate(avg_avancement=models.Avg('avancement'))['avg_avancement']
            return round(avg or 0, 1)
        return 0


# serializers.py
from rest_framework import serializers
from .models import Client

class ClientSerializer(serializers.ModelSerializer):
    status_label = serializers.SerializerMethodField()
    
    class Meta:
        model = Client
        fields = [
            'id', 
            'nom', 
            'email', 
            'telephone', 
            'photo_profil',
            'entreprise',        # ← au lieu de 'societe'
            'poste',
            'statut_approbation',
            'status_label',
            'justification_rejet',
            'date_creation', 
            'actif'
        ]
        read_only_fields = ['id', 'date_creation', 'statut_approbation']
    
    def get_status_label(self, obj):
        labels = {
            'pending': 'En attente',
            'approved': 'Approuvé',
            'rejected': 'Rejeté',
            None: 'En attente'
        }
        return labels.get(getattr(obj, 'statut_approbation', None), 'En attente')


class PartenaireSerializer(serializers.ModelSerializer):
    class Meta:
        model = Partenaire
        fields = ['id', 'nom', 'email', 'telephone', 'photo_profil',
                    'date_debut_partenariat', 'date_fin_partenariat', 'date_creation', 'actif']
        read_only_fields = ['id', 'date_creation', 'date_debut_partenariat']


# ========== PROJET & TÂCHES ==========

class ProjetSerializer(serializers.ModelSerializer):
    client_nom = serializers.ReadOnlyField(source='client.nom', default=None)
    chef_projet_nom = serializers.ReadOnlyField(source='chef_projet.nom', default=None)
    partenaires_noms = serializers.SerializerMethodField()
    avancement_globale = serializers.SerializerMethodField()  # ← Écrase le champ existant
    nombre_membres = serializers.SerializerMethodField()
    
    class Meta:
        model = Projet
        fields = ['id', 'tenant', 'nom', 'description', 'objectsif', 'date_debut',
                  'date_fin_prevue', 'date_fin_reelle', 'budget', 'statut',
                  'avancement_globale', 'client', 'client_nom', 'chef_projet',
                  'chef_projet_nom', 'partenaires', 'partenaires_noms', 'domaine','nombre_membres']
        read_only_fields = ['id', 'tenant']
    
    def get_partenaires_noms(self, obj):
        return [p.nom for p in obj.partenaires.all()]
    def get_avancement_globale(self, obj):
        """Calcule l'avancement moyen des tâches du projet"""
        taches = obj.taches.all()
        if taches.exists():
            avg = taches.aggregate(avg_avancement=Avg('avancement'))['avg_avancement']
            return round(avg or 0, 1)
        return 0
    def get_nombre_membres(self, obj):
        """Calcule le nombre total de membres (chef + consultants)"""
        membres = set()
        
        # Ajouter le chef de projet
        if obj.chef_projet_id:
            membres.add(obj.chef_projet_id)
        
        # Ajouter les consultants uniques des tâches
        consultants_ids = obj.taches.values_list('consultant_id', flat=True).distinct()
        membres.update(consultants_ids)
        
        return len(membres)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pour le formulaire HTML de DRF, limiter les choix aux utilisateurs avec rôle partenaire
        if 'request' in self.context:
            tenant = self.context['request'].tenant
            self.fields['partenaires'].queryset = Utilisateur.objects.filter(
                role='partenaire',
                memberships__tenant=tenant
            )

    # serializers.py
from rest_framework import serializers
from django.db import models
from .models import Tache, Notification, Utilisateur, Projet
from .services.notification_service import NotificationService

# serializers.py
from rest_framework import serializers
from django.db import models
from .models import Tache, Notification, Utilisateur, Projet
from .services.notification_service import NotificationService

class TacheSerializer(serializers.ModelSerializer):
    projet_nom = serializers.ReadOnlyField(source='projet.nom')
    consultant_nom = serializers.ReadOnlyField(source='consultant.nom', default=None)
    
    class Meta:
        model = Tache
        fields = ['id', 'tenant', 'titre', 'description', 'priorite', 'avancement',
                  'date_debut', 'date_fin_prevue', 'date_fin_reelle', 'statut',
                  'projet', 'projet_nom', 'consultant', 'consultant_nom']
        read_only_fields = ['id', 'tenant']

    def update(self, instance, validated_data):

        print("=" * 50)
        print("🔍 [SERIALIZER] update() appelé")

        # Sauvegarder les anciennes valeurs
        ancien_statut = instance.statut
        ancien_avancement = instance.avancement
        ancien_titre = instance.titre
        ancien_consultant = instance.consultant
        ancien_priorite = instance.priorite
        
        nouvel_statut = validated_data.get('statut', instance.statut)
        nouvel_avancement = validated_data.get('avancement', instance.avancement)
        nouvel_titre = validated_data.get('titre', instance.titre)
        nouvel_consultant = validated_data.get('consultant', instance.consultant)
        nouvel_priorite = validated_data.get('priorite', instance.priorite)

        print(f"🔍 [SERIALIZER] Tâche: {instance.titre}")
        print(f"🔍 [SERIALIZER] Ancien statut: '{ancien_statut}'")
        print(f"🔍 [SERIALIZER] Nouveau statut: '{nouvel_statut}'")
        print(f"🔍 [SERIALIZER] Changement statut: {ancien_statut != nouvel_statut}")
        
        # Liste des champs modifiés (pour notification générale)
        champs_modifies = []
        if ancien_titre != nouvel_titre:
            champs_modifies.append("titre")
        if ancien_consultant != nouvel_consultant:
            champs_modifies.append("consultant assigné")
        if ancien_priorite != nouvel_priorite:
            champs_modifies.append("priorité")
        
        # ✅ Logique d'avancement automatique selon le statut
        if nouvel_statut == 'a_faire':
            validated_data['avancement'] = 0
        elif nouvel_statut == 'termine':
            validated_data['avancement'] = 100
        
        # Sauvegarde
        instance = super().update(instance, validated_data)
        
        # Récupérer l'utilisateur depuis le contexte
        request = self.context.get('request')
        print(f"🔍 [SERIALIZER] Contexte request présent: {request is not None}")
        utilisateur = request.user if request and hasattr(request, 'user') else None
        
        if not utilisateur:
            return instance
        
        # ✅ NOTIFICATION : Changement de statut
        if ancien_statut != nouvel_statut:
            NotificationService.notifier_changement_statut_tache(
                tache=instance,
                ancien_statut=ancien_statut,
                nouveau_statut=nouvel_statut,
                utilisateur=utilisateur
            )
        
        # ✅ NOTIFICATION : Modification générale
        if champs_modifies:
            NotificationService.notifier_modification_tache(
                tache=instance,
                utilisateur=utilisateur,
                champs_modifies=champs_modifies
            )
        
        # ✅ NOTIFICATION : Avancement significatif (25% ou plus)
        if abs(nouvel_avancement - ancien_avancement) >= 25:
            NotificationService.notifier_avancement_tache(
                tache=instance,
                ancien_avancement=ancien_avancement,
                nouvel_avancement=nouvel_avancement,
                utilisateur=utilisateur
            )
        
        # ✅ Mettre à jour l'avancement du projet
        self.mettre_a_jour_avancement_projet(instance.projet)
        
        return instance
    def create(self, validated_data):
    
    
    # ✅ Ajouter le tenant
        request = self.context.get('request')
        if request and hasattr(request, 'tenant'):
            validated_data['tenant'] = request.tenant
            print(f"🔍 Tenant ajouté: {request.tenant}")
    
    # ✅ UNE SEULE CRÉATION
        instance = super().create(validated_data)
        print(f"🔍 Instance créée avec ID: {instance.id}")
    
      # ✅ NOTIFICATION : Nouvelle tâche créée
        utilisateur = request.user if request and hasattr(request, 'user') else None
        if utilisateur:
            NotificationService.notifier_creation_tache(
                tache=instance,
                utilisateur=utilisateur
            )
    
    

    
    def delete(self, instance):
        """Méthode appelée avant la suppression"""
        projet = instance.projet
        
        # Récupérer l'utilisateur depuis le contexte
        request = self.context.get('request')
        utilisateur = request.user if request and hasattr(request, 'user') else None
        
        # ✅ NOTIFICATION : Suppression de tâche
        if utilisateur:
            NotificationService.notifier_suppression_tache(
                tache=instance,
                utilisateur=utilisateur
            )
        
        # Mettre à jour l'avancement du projet après suppression
        self.mettre_a_jour_avancement_projet(projet)
        
        return instance
    
    def mettre_a_jour_avancement_projet(self, projet):
        """Met à jour l'avancement du projet et son statut"""
        taches = projet.taches.all()
        if taches.exists():
            # Calculer l'avancement moyen
            avancement_moyen = taches.aggregate(
                avg_avancement=models.Avg('avancement')
            )['avg_avancement'] or 0
            
            projet.avancement_globale = round(avancement_moyen, 1)
            
            # Logique : Si avancement = 100% et toutes les tâches sont terminées
            toutes_terminees = all(t.statut == 'termine' for t in taches)
            
            if projet.avancement_globale == 100 and toutes_terminees:
                if projet.statut != 'termine':
                    projet.statut = 'termine'
                    self.creer_notification_fin_projet(projet)
            elif projet.avancement_globale < 100 and projet.statut == 'termine':
                projet.statut = 'en_cours'
            
            projet.save()
    
    def creer_notification_fin_projet(self, projet):
        """Notification quand un projet est terminé"""
        # Notifier la direction
        direction_users = Utilisateur.objects.filter(role='direction')
        for destinataire in direction_users:
            Notification.objects.create(
                tenant=projet.tenant,
                utilisateur=destinataire,
                titre=f"🏆 Projet terminé - {projet.nom}",
                message=f"Le projet '{projet.nom}' est maintenant terminé avec 100% d'avancement.",
                type='succes',
                lien_action=f"/app/projets/{projet.id}",
                entite_id=projet.id,
                entite_type='projet',
                projet=projet
            )
        
        # Notifier aussi le chef de projet
        if projet.chef_projet:
            Notification.objects.create(
                tenant=projet.tenant,
                utilisateur=projet.chef_projet,
                titre=f"🏆 Projet terminé - {projet.nom}",
                message=f"Le projet '{projet.nom}' est maintenant terminé avec 100% d'avancement.",
                type='succes',
                lien_action=f"/app/projets/{projet.id}",
                entite_id=projet.id,
                entite_type='projet',
                projet=projet
            )

class SousTacheSerializer(serializers.ModelSerializer):
    tache_titre = serializers.ReadOnlyField(source='tache.titre')
    
    class Meta:
        model = SousTache
        fields = ['id', 'tenant', 'titre', 'statut', 'avancement', 'date_echeance',
                  'tache', 'tache_titre']
        read_only_fields = ['id', 'tenant']


# ========== DOCUMENTS & COMMENTAIRES ==========


class DocumentSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='nom', read_only=True)
    description = serializers.CharField(read_only=True)
    path = serializers.CharField(source='chemin', read_only=True)
    type = serializers.CharField(source='type_fichier', read_only=True)
    projectId = serializers.UUIDField(source='projet.id', read_only=True)
    projectName = serializers.CharField(source='projet.nom', read_only=True)
    uploadBy = serializers.UUIDField(source='upload_par.id', read_only=True)
    uploadByName = serializers.CharField(source='upload_par.nom', read_only=True)
    uploadAt = serializers.DateTimeField(source='date_upload', read_only=True)
    size = serializers.IntegerField(source='taille', read_only=True)
    
    class Meta:
        model = Document
        fields = ['id', 'name', 'description', 'path', 'version', 'type', 
                  'projectId', 'projectName', 'uploadBy', 'uploadByName', 
                  'uploadAt', 'size']
        read_only_fields = ['id', 'uploadAt', 'uploadBy', 'uploadByName']

    def create(self, validated_data):
        # Ajouter l'utilisateur connecté
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['upload_par'] = request.user
        
        instance = super().create(validated_data)
        
        # ✅ NOTIFICATION : Nouveau document uploadé
        self.notifier_nouveau_document(instance, request.user)
        
        return instance
    
    def update(self, instance, validated_data):
        ancien_nom = instance.nom
        nouvel_nom = validated_data.get('nom', instance.nom)
        
        instance = super().update(instance, validated_data)
        
        request = self.context.get('request')
        utilisateur = request.user if request else None
        
        # ✅ NOTIFICATION : Document modifié
        if ancien_nom != nouvel_nom and utilisateur:
            self.notifier_modification_document(instance, utilisateur, ancien_nom)
        
        return instance
    
    def delete(self, instance):
        request = self.context.get('request')
        utilisateur = request.user if request else None
        
        # ✅ NOTIFICATION : Document supprimé
        if utilisateur:
            self.notifier_suppression_document(instance, utilisateur)
        
        return super().delete(instance)
    
    def notifier_nouveau_document(self, document, utilisateur):
        """Notification lors de l'upload d'un nouveau document"""
        titre = f"📄 Nouveau document - {document.projet.nom}"
        message = f"{utilisateur.nom} a téléversé '{document.nom}'"
        
        # Déterminer le type de notification
        type_notif = 'succes' if document.type_fichier == 'livrable' else 'info'
        
        # Destinataires
        destinataires = set()
        
        # Ajouter le chef de projet
        if document.projet.chef_projet and document.projet.chef_projet != utilisateur:
            destinataires.add(document.projet.chef_projet)
        
        # Ajouter la direction
        direction_users = Utilisateur.objects.filter(role='direction')
        for user in direction_users:
            if user != utilisateur:
                destinataires.add(user)
        
        # Si c'est un livrable, notifier aussi le client
        if document.type_fichier == 'livrable' and document.projet.client:
            if document.projet.client != utilisateur:
                destinataires.add(document.projet.client)
        
        # Créer les notifications
        for destinataire in destinataires:
            NotificationService.creer_notification(
                utilisateur=destinataire,
                titre=titre,
                message=message,
                type_notif=type_notif,
                lien_action=f"/app/documents/{document.id}",
                entite_id=document.id,
                entite_type='document',
                projet=document.projet
            )
    
    def notifier_modification_document(self, document, utilisateur, ancien_nom):
        """Notification lors de la modification d'un document"""
        titre = f"✏️ Document modifié - {document.projet.nom}"
        message = f"{utilisateur.nom} a modifié '{document.nom}' (anciennement '{ancien_nom}')"
        
        # Destinataires
        destinataires = set()
        
        if document.projet.chef_projet and document.projet.chef_projet != utilisateur:
            destinataires.add(document.projet.chef_projet)
        
        direction_users = Utilisateur.objects.filter(role='direction')
        for user in direction_users:
            if user != utilisateur:
                destinataires.add(user)
        
        for destinataire in destinataires:
            NotificationService.creer_notification(
                utilisateur=destinataire,
                titre=titre,
                message=message,
                type_notif='info',
                lien_action=f"/app/documents/{document.id}",
                entite_id=document.id,
                entite_type='document',
                projet=document.projet
            )
    
    def notifier_suppression_document(self, document, utilisateur):
        """Notification lors de la suppression d'un document"""
        titre = f"🗑️ Document supprimé - {document.projet.nom}"
        message = f"{utilisateur.nom} a supprimé le document '{document.nom}'"
        
        destinataires = set()
        
        if document.projet.chef_projet and document.projet.chef_projet != utilisateur:
            destinataires.add(document.projet.chef_projet)
        
        direction_users = Utilisateur.objects.filter(role='direction')
        for user in direction_users:
            if user != utilisateur:
                destinataires.add(user)
        
        for destinataire in destinataires:
            NotificationService.creer_notification(
                utilisateur=destinataire,
                titre=titre,
                message=message,
                type_notif='attention',
                lien_action=f"/app/projets/{document.projet.id}",
                entite_id=document.projet.id,
                entite_type='projet',
                projet=document.projet
            )


class CommentaireSerializer(serializers.ModelSerializer):
    utilisateur_nom = serializers.ReadOnlyField(source='utilisateur.nom')
    tache_titre = serializers.ReadOnlyField(source='tache.titre')
    
    class Meta:
        model = Commentaire
        fields = ['id', 'tenant', 'contenu', 'date_publication', 'utilisateur',
                  'utilisateur_nom', 'tache', 'tache_titre']
        read_only_fields = ['id', 'tenant', 'date_publication']


# ========== NOTIFICATIONS ==========

class NotificationSerializer(serializers.ModelSerializer):
    utilisateur_nom = serializers.ReadOnlyField(source='utilisateur.nom')
    
    class Meta:
        model = Notification
        fields = ['id', 'tenant', 'type', 'titre', 'message', 'lue',
                  'date_envoi', 'utilisateur', 'utilisateur_nom']
        read_only_fields = ['id', 'tenant', 'date_envoi']


# ========== CONVERSATIONS & MESSAGES ==========

class ConversationSerializer(serializers.ModelSerializer):
    projet_nom = serializers.ReadOnlyField(source='projet.nom')
    dernier_message = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = ['id', 'tenant', 'titre', 'date_creation', 'date_dernier_message',
                  'projet', 'projet_nom', 'dernier_message']
        read_only_fields = ['id', 'tenant', 'date_creation', 'date_dernier_message']
    
    def get_dernier_message(self, obj):
        dernier = obj.messages.order_by('-date_envoi').first()
        if dernier:
            return {
                'contenu': dernier.contenu[:50],
                'date': dernier.date_envoi,
                'expediteur': dernier.expediteur.nom
            }
        return None


class MessageSerializer(serializers.ModelSerializer):
    expediteur_nom = serializers.ReadOnlyField(source='expediteur.nom')
    
    class Meta:
        model = Message
        fields = ['id', 'tenant', 'contenu', 'date_envoi', 'lu', 'type_message',
                  'conversation', 'expediteur', 'expediteur_nom']
        read_only_fields = ['id', 'tenant', 'date_envoi']


# ========== KPI & BUDGET ==========

class KpiSerializer(serializers.ModelSerializer):
    projet_nom = serializers.ReadOnlyField(source='projet.nom')
    
    class Meta:
        model = Kpi
        fields = ['id', 'tenant', 'nom', 'valeur_cible', 'valeur_actuelle',
                  'unite', 'seuil_alerte', 'projet', 'projet_nom']
        read_only_fields = ['id', 'tenant']


class BudgetSerializer(serializers.ModelSerializer):
    projet_nom = serializers.ReadOnlyField(source='projet.nom')
    
    class Meta:
        model = Budget
        fields = ['id', 'tenant', 'montant_total', 'montant_depense', 
                  'montant_restant', 'devise', 'projet', 'projet_nom']
        read_only_fields = ['id', 'tenant']


# ========== RESSOURCES ==========

class RessourceSerializer(serializers.ModelSerializer):
    projets_noms = serializers.SerializerMethodField()
    
    class Meta:
        model = Ressource
        fields = ['id', 'tenant', 'type', 'nom', 'cout_unitaire', 'disponible', 
                  'projet', 'projets_noms']
        read_only_fields = ['id', 'tenant']
    
    def get_projets_noms(self, obj):
        return [p.nom for p in obj.projet.all()]
    

# ramaqs_management_plateforme/serializers.py

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from rest_framework import serializers

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    
    def validate(self, attrs):
        # Récupérer l'email et le password
        email = attrs.get('email', attrs.get('username'))
        password = attrs.get('password')
        print(f"🔐 Tentative de connexion: email={email}")
        
        # Authentifier avec l'email
        user = authenticate(username=email, password=password)
        
        if not user:
            print(f"❌ Utilisateur non trouvé ou mot de passe incorrect: {email}")
            raise serializers.ValidationError('Email ou mot de passe incorrect')
        
        if not user.is_active:
            print(f"❌ Compte désactivé: {email}")
            raise serializers.ValidationError('Compte désactivé')
        
        print(f"✅ Utilisateur authentifié: {user.email}, rôle: {user.role}")
        
        # Générer les tokens
        refresh = RefreshToken.for_user(user)
        
        # Récupérer le membership
        membership = None
        if hasattr(user, 'memberships') and user.memberships.exists():
            membership = user.memberships.first()
        
        # ✅ STRUCTURE DE RÉPONSE CORRECTE (sans doublons)
        data = {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': str(user.id),
                'nom': user.nom,
                'email': user.email,
                'role': membership.role if membership else user.role,
                'is_active': user.is_active,
                'statut_approbation': getattr(user, 'statut_approbation', None),
            }
        }
        
        # Ajouter les infos tenant si disponible
        if membership and membership.tenant:
            data['tenant'] = {
                'id': str(membership.tenant.id),
                'nom': membership.tenant.nom,
                'slug': getattr(membership.tenant, 'slug', None),
            }
        
        print(f"✅ Connexion réussie pour {user.email}")
        print(f"📤 Réponse envoyée: access={data['access'][:50]}...")
        
        return data