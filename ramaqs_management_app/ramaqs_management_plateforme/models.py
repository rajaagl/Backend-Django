from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid
from .managers import TenantManager
from django.utils import timezone
from .utils import get_current_tenant

# ========== RÔLES DÉFINIS ==========

class RoleChoices(models.TextChoices):
    """Les 6 rôles de votre plateforme"""
    SUPER_ADMIN = 'super_admin', 'Super Administrateur RAMAQS'
    DIRECTION = 'direction', 'Direction RAMAQS'
    CHEF_PROJET = 'chef_projet', 'Chef de projet'
    CONSULTANT = 'consultant', 'Consultant'
    CLIENT = 'client', 'Client'
    PARTENAIRE = 'partenaire', 'Partenaire'


# ========== TENANT ==========

class Tenant(models.Model):
    """Tenant = Espace client (entreprise cliente)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, max_length=100)
    secteur_activite = models.CharField(max_length=100, blank=True, null=True)
    logo = models.URLField(blank=True, null=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    actif = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'tenants'
    
    def __str__(self):
        return self.nom


class TenantMembership(models.Model):
    """Relation User - Tenant avec rôle spécifique"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('Utilisateur', on_delete=models.CASCADE, related_name='memberships')
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='memberships')
    role = models.CharField(max_length=20, choices=RoleChoices.choices)
    date_joined = models.DateTimeField(auto_now_add=True)
    invite_par = models.ForeignKey('Utilisateur', on_delete=models.SET_NULL, null=True, blank=True, related_name='invitations')
    
    class Meta:
        db_table = 'tenant_memberships'
        unique_together = [['user', 'tenant']]
    
    def __str__(self):
        return f"{self.user.email} - {self.tenant.nom} ({self.role})"


# ========== UTILISATEUR ==========

class Utilisateur(AbstractUser):
    """Modèle utilisateur unifié"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom = models.CharField(max_length=100)
    telephone = models.CharField(max_length=20, blank=True, null=True)
    photo_profil = models.ImageField(upload_to='photos_profils/', null=True, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    dernier_connexion = models.DateTimeField(auto_now=True)
    actif = models.BooleanField(default=True)
    entreprise = models.CharField(max_length=100, blank=True, null=True)
    poste = models.CharField(max_length=100, blank=True, null=True)
    ROLE_CHOICES = [
        ('direction', 'Direction'),
        ('chef_projet', 'Chef de projet'),
        ('consultant', 'Consultant'),
        ('client', 'Client'),
        ('partenaire', 'Partenaire'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='consultant') 
    date_debut_partenariat = models.DateField(blank=True, null=True)
    date_fin_partenariat = models.DateField(blank=True, null=True)
    
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='utilisateur_set',
        blank=True,
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='utilisateur_set',
        blank=True,
    )
    
    class Meta:
         db_table = 'ramaqs_management_plateforme_utilisateur'  # ← Nom exact de votre table
    
    def __str__(self):
        return self.email
    
    def get_role_in_tenant(self, tenant):
        try:
            membership = self.memberships.get(tenant=tenant)
            return membership.role
        except TenantMembership.DoesNotExist:
            return None
    
    def has_permission(self, tenant, required_role):
        role = self.get_role_in_tenant(tenant)
        if not role:
            return False
        
        hierarchy = {
            RoleChoices.SUPER_ADMIN: 6,
            RoleChoices.DIRECTION: 5,
            RoleChoices.CHEF_PROJET: 4,
            RoleChoices.CONSULTANT: 3,
            RoleChoices.PARTENAIRE: 2,
            RoleChoices.CLIENT: 1,
        }
        
        return hierarchy.get(role, 0) >= hierarchy.get(required_role, 0)
    
    def is_super_admin(self):
        return self.is_superuser or self.memberships.filter(role=RoleChoices.SUPER_ADMIN).exists()


# ========== MODÈLES SPÉCIFIQUES (PROXY) ==========

class Direction(Utilisateur):
    class Meta:
        proxy = True
    
    def __str__(self):
        return f"{self.nom} - Direction"


class ChefProjet(Utilisateur):
    class Meta:
        proxy = True
    
    def __str__(self):
        return f"{self.nom} - Chef de projet"


class Consultant(Utilisateur):
    
    class Meta:
        proxy = True
    
    def __str__(self):
        return f"{self.nom} - Consultant"


class Client(Utilisateur):
    class Meta:
        proxy = True
    
    def __str__(self):
        return f"{self.nom} - Client"


class Partenaire(Utilisateur):
    class Meta:
        proxy = True
    
    def __str__(self):
        return f"{self.nom} - Partenaire"


# ========== MODÈLES MÉTIER ==========

class Projet(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='projets')
    nom = models.CharField(max_length=100)
    description = models.TextField()
    objectsif = models.CharField(max_length=100)
    date_debut = models.DateField()
    date_fin_prevue = models.DateField()
    date_fin_reelle = models.DateField(null=True, blank=True)
    budget = models.DecimalField(max_digits=10, decimal_places=2)
    statut = models.CharField(max_length=50)
    avancement_globale = models.DecimalField(max_digits=5, decimal_places=2)
    client = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='projets_client')
    chef_projet = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='projets_chef')
    partenaires = models.ManyToManyField(Utilisateur, related_name='projets_partenaire', limit_choices_to={'role': 'partenaire'})
    domaine = models.CharField(max_length=100)
    priorite = models.CharField(max_length=50)
    
    objects = TenantManager()
    
    class Meta:
        db_table = 'projets'
        indexes = [
            models.Index(fields=['tenant', 'statut']),
            models.Index(fields=['tenant', 'date_debut']),
        ]
    
    def __str__(self):
        return f"{self.nom} - {self.tenant.nom}"


class Tache(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    titre = models.CharField(max_length=100)
    description = models.TextField()
    priorite = models.CharField(max_length=50)
    avancement = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    date_debut = models.DateField()
    date_fin_prevue = models.DateField()
    date_fin_reelle = models.DateField(null=True, blank=True)
    statut = models.CharField(max_length=50)
    projet = models.ForeignKey(Projet, on_delete=models.CASCADE, related_name='taches')
    consultant = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='taches')
    
    objects = TenantManager()
    
    class Meta:
        db_table = 'taches'
        indexes = [
            models.Index(fields=['tenant', 'statut']),
            models.Index(fields=['tenant', 'consultant']),
        ]
    
    def __str__(self):
        return self.titre


class SousTache(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    titre = models.CharField(max_length=100)
    statut = models.CharField(max_length=50)
    avancement = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    date_echeance = models.DateField()
    tache = models.ForeignKey(Tache, on_delete=models.CASCADE, related_name='sous_taches')
    
    objects = TenantManager()
    
    class Meta:
        db_table = 'sous_taches'
    
    def __str__(self):
        return self.titre


class Commentaire(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    contenu = models.TextField()
    date_publication = models.DateTimeField(auto_now_add=True)
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE)
    tache = models.ForeignKey(Tache, on_delete=models.CASCADE, related_name='commentaires')
    
    objects = TenantManager()
    
    class Meta:
        db_table = 'commentaires'
    
    def __str__(self):
        return f"Commentaire de {self.utilisateur.nom}"


class Document(models.Model):
    TYPE_CHOICES = [
        ('document', 'Document'),
        ('livrable', 'Livrable'),
        ('rapport', 'Rapport'),
        ('contrat', 'Contrat'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    nom = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)  # ✅ AJOUTER
    chemin = models.FileField(upload_to='documents/')
    version = models.CharField(max_length=20)
    taille = models.IntegerField()
    type_fichier = models.CharField(max_length=50, choices=TYPE_CHOICES, default='document')  # ✅ MODIFIER
    date_upload = models.DateTimeField(auto_now_add=True)
    projet = models.ForeignKey(Projet, on_delete=models.CASCADE, related_name='documents')
    upload_par = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, blank=True, related_name='documents')  # ✅ AJOUTER
    
    objects = TenantManager()
    
    class Meta:
        db_table = 'documents'
        ordering = ['-date_upload']
    
    def __str__(self):
        return self.nom


class Ressource(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    type = models.CharField(max_length=50)
    nom = models.CharField(max_length=100)
    cout_unitaire = models.DecimalField(max_digits=10, decimal_places=2)
    disponible = models.BooleanField(default=True)
    projet = models.ManyToManyField(Projet, related_name='ressources')
    
    objects = TenantManager()
    
    class Meta:
        db_table = 'ressources'
    
    def __str__(self):
        return self.nom


class Notification(models.Model):
    TYPE_CHOICES = [
        ('info', 'Information'),
        ('succes', 'Succès'),
        ('attention', 'Attention'),
        ('erreur', 'Erreur'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    type = models.CharField(max_length=100, choices=TYPE_CHOICES, default='info')
    titre = models.CharField(max_length=200)
    message = models.CharField(max_length=200)
    lue = models.BooleanField(default=False)
    date_envoi = models.DateTimeField(auto_now_add=True)
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='notifications')
    # ✅ NOUVEAUX CHAMPS
    lien_action = models.CharField(max_length=500, blank=True, null=True)  # Lien vers la ressource concernée
    entite_id = models.UUIDField(null=True, blank=True)  # ID de l'entité (tâche, projet, etc.)
    entite_type = models.CharField(max_length=50, blank=True, null=True)  # Type d'entité ('tache', 'projet')
    # models.py - Ajouter dans Notification
    projet = models.ForeignKey('Projet', on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    objects = TenantManager()
    
    class Meta:
        db_table = 'notifications'
        indexes = [
            models.Index(fields=['tenant', 'utilisateur', 'lue']),
            models.Index(fields=['tenant', 'utilisateur', '-date_envoi']),
        ]
        ordering = ['-date_envoi']
    
    def __str__(self):
        return self.titre

    @classmethod
    def creer_notification(cls, utilisateur, titre, message, type_notif='info', lien_action=None, entite_id=None, entite_type=None):
        """Méthode utilitaire pour créer une notification"""
        
        tenant = get_current_tenant()
        
        return cls.objects.create(
            tenant=tenant,
            utilisateur=utilisateur,
            titre=titre,
            message=message,
            type=type_notif,
            lien_action=lien_action,
            entite_id=entite_id,
            entite_type=entite_type
        )

class Kpi(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    nom = models.CharField(max_length=50)
    valeur_cible = models.FloatField()
    valeur_actuelle = models.FloatField()
    unite = models.CharField(max_length=255)
    seuil_alerte = models.FloatField()
    projet = models.ForeignKey(Projet, on_delete=models.CASCADE, related_name='kpis')
    
    objects = TenantManager()
    
    class Meta:
        db_table = 'kpis'
    
    def __str__(self):
        return self.nom


class Conversation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    titre = models.CharField(max_length=255)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_dernier_message = models.DateTimeField(auto_now=True)
    projet = models.ForeignKey(Projet, on_delete=models.CASCADE, related_name='conversations')
    
    objects = TenantManager()
    
    class Meta:
        db_table = 'conversations'
    
    def __str__(self):
        return self.titre


class Message(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    contenu = models.TextField()
    date_envoi = models.DateTimeField(auto_now_add=True)
    lu = models.BooleanField(default=False)
    type_message = models.CharField(max_length=50, default='texte')
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    expediteur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='messages_envoyes')
    
    objects = TenantManager()
    
    class Meta:
        db_table = 'messages'
        indexes = [
            models.Index(fields=['tenant', 'conversation', 'date_envoi']),
        ]
    
    def __str__(self):
        return f"Message de {self.expediteur.nom}"


class Budget(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    montant_total = models.FloatField()
    montant_depense = models.FloatField()
    montant_restant = models.FloatField()
    devise = models.CharField(max_length=10, default='EUR')
    projet = models.ForeignKey(Projet, on_delete=models.CASCADE, related_name='budgets')
    
    objects = TenantManager()
    
    class Meta:
        db_table = 'budgets'
    
    def __str__(self):
        return f"Budget {self.projet.nom} - {self.montant_total} {self.devise}"


class PasswordResetToken(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='reset_tokens')
    token = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'password_reset_tokens'
    
    def is_valid(self):
        return not self.used and self.expires_at > timezone.now()
    
    def __str__(self):
        return f"Reset token for {self.user.email}"