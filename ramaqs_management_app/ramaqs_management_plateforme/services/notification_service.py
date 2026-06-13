# services/notification_service.py
from ..models import Notification, Utilisateur
from ..utils.tenant import get_current_tenant

class NotificationService:
    
    @staticmethod
    def creer_notification(utilisateur, titre, message, type_notif='info', lien_action=None, entite_id=None, entite_type=None, projet=None):
        """Méthode utilitaire pour créer une notification"""
        tenant = get_current_tenant()
        
        return Notification.objects.create(
            tenant=tenant,
            utilisateur=utilisateur,
            titre=titre,
            message=message,
            type=type_notif,
            lien_action=lien_action,
            entite_id=entite_id,
            entite_type=entite_type,
            projet=projet
        )
    
    # ========== NOTIFICATIONS TÂCHES ==========
    
    @staticmethod
    def notifier_creation_tache(tache, utilisateur):
        """Notification lors de la création d'une tâche"""
        titre = f"➕ Nouvelle tâche - {tache.projet.nom}"
        message = f"La tâche '{tache.titre}' a été créée par {utilisateur.nom}"
        
        # Notifier le chef de projet
        if tache.projet.chef_projet and tache.projet.chef_projet != utilisateur:
            NotificationService.creer_notification(
                utilisateur=tache.projet.chef_projet,
                titre=titre,
                message=message,
                type_notif='info',
                lien_action=f"/app/taches/{tache.id}",
                entite_id=tache.id,
                entite_type='tache',
                projet=tache.projet
            )
        
        # Notifier la direction
        direction_users = Utilisateur.objects.filter(role='direction')
        for user in direction_users:
            if user != utilisateur:
                NotificationService.creer_notification(
                    utilisateur=user,
                    titre=titre,
                    message=message,
                    type_notif='info',
                    lien_action=f"/app/taches/{tache.id}",
                    entite_id=tache.id,
                    entite_type='tache',
                    projet=tache.projet
                )
    
    @staticmethod
    def notifier_modification_tache(tache, utilisateur, champs_modifies):
        """Notification lors de la modification d'une tâche"""
        titre = f"✏️ Tâche modifiée - {tache.projet.nom}"
        message = f"La tâche '{tache.titre}' a été modifiée par {utilisateur.nom}"
        
        if champs_modifies:
            message += f" - {', '.join(champs_modifies)}"
        
        # Notifier le chef de projet
        if tache.projet.chef_projet and tache.projet.chef_projet != utilisateur:
            NotificationService.creer_notification(
                utilisateur=tache.projet.chef_projet,
                titre=titre,
                message=message,
                type_notif='info',
                lien_action=f"/app/taches/{tache.id}",
                entite_id=tache.id,
                entite_type='tache',
                projet=tache.projet
            )
    
    @staticmethod
    def notifier_changement_statut_tache(tache, ancien_statut, nouveau_statut, utilisateur):
        """Notification lors du changement de statut d'une tâche"""

        print("-" * 40)
        print("🔔 [NOTIFICATION] notifier_changement_statut_tache")
        print(f"🔔 Tâche: {tache.titre}")
        print(f"🔔 Ancien statut: {ancien_statut}")
        print(f"🔔 Nouveau statut: {nouveau_statut}")
        print(f"🔔 Utilisateur: {utilisateur.nom if utilisateur else 'None'}")



        status_labels = {
            'a_faire': 'À faire',
            'en cours': 'En cours',
            'termine': 'Terminé'
        }
        
        titre = f"🔄 Statut changé - {tache.projet.nom}"
        message = f"La tâche '{tache.titre}' est passée de '{status_labels.get(ancien_statut, ancien_statut)}' à '{status_labels.get(nouveau_statut, nouveau_statut)}'"
        
        type_notif = 'succes' if nouveau_statut == 'termine' else 'info'
        
        print(f"🔔 Titre notification: {titre}")
        print(f"🔔 Message: {message}")

        
        
        # Notifier le chef de projet si différent
        if tache.projet.chef_projet and tache.projet.chef_projet != utilisateur:
            NotificationService.creer_notification(
                utilisateur=tache.projet.chef_projet,
                titre=titre,
                message=message,
                type_notif='info',
                lien_action=f"/app/taches/{tache.id}",
                entite_id=tache.id,
                entite_type='tache',
                projet=tache.projet
            )
        
        # Notifier la direction
        direction_users = Utilisateur.objects.filter(role='direction')
        for user in direction_users:
            if user != utilisateur and (not tache.projet.chef_projet or user != tache.projet.chef_projet):
                NotificationService.creer_notification(
                    utilisateur=user,
                    titre=titre,
                    message=message,
                    type_notif='info',
                    lien_action=f"/app/taches/{tache.id}",
                    entite_id=tache.id,
                    entite_type='tache',
                    projet=tache.projet
                )
    
    @staticmethod
    def notifier_avancement_tache(tache, ancien_avancement, nouvel_avancement, utilisateur):
        """Notification lors d'un changement d'avancement significatif"""
        if tache.projet.chef_projet:
            titre = f"📊 Progression - {tache.projet.nom}"
            message = f"La tâche '{tache.titre}' est passée de {ancien_avancement}% à {nouvel_avancement}%"
            
            NotificationService.creer_notification(
                utilisateur=tache.projet.chef_projet,
                titre=titre,
                message=message,
                type_notif='info',
                lien_action=f"/app/taches/{tache.id}",
                entite_id=tache.id,
                entite_type='tache',
                projet=tache.projet
            )
    
    @staticmethod
    def notifier_suppression_tache(tache, utilisateur):
        """Notification lors de la suppression d'une tâche"""
        titre = f"🗑️ Tâche supprimée - {tache.projet.nom}"
        message = f"La tâche '{tache.titre}' a été supprimée par {utilisateur.nom}"
        
        if tache.projet.chef_projet and tache.projet.chef_projet != utilisateur:
            NotificationService.creer_notification(
                utilisateur=tache.projet.chef_projet,
                titre=titre,
                message=message,
                type_notif='attention',
                lien_action=f"/app/projets/{tache.projet.id}",
                entite_id=tache.projet.id,
                entite_type='projet',
                projet=tache.projet
            )
    
    # ========== NOTIFICATIONS PROJETS ==========
    
    @staticmethod
    def notifier_creation_projet(projet, utilisateur):
        """Notification lors de la création d'un projet"""
        titre = f"➕ Nouveau projet - {projet.nom}"
        message = f"Le projet '{projet.nom}' a été créé par {utilisateur.nom}"
        
        # Notifier la direction
        direction_users = Utilisateur.objects.filter(role='direction')
        for user in direction_users:
            if user != utilisateur:
                NotificationService.creer_notification(
                    utilisateur=user,
                    titre=titre,
                    message=message,
                    type_notif='succes',
                    lien_action=f"/app/projets/{projet.id}",
                    entite_id=projet.id,
                    entite_type='projet',
                    projet=projet
                )
        
        # Notifier le chef de projet (si différent de l'utilisateur)
        if projet.chef_projet and projet.chef_projet != utilisateur:
            NotificationService.creer_notification(
                utilisateur=projet.chef_projet,
                titre=titre,
                message=message,
                type_notif='info',
                lien_action=f"/app/projets/{projet.id}",
                entite_id=projet.id,
                entite_type='projet',
                projet=projet
            )
    
    @staticmethod
    def notifier_modification_projet(projet, utilisateur, champs_modifies):
        """Notification lors de la modification d'un projet"""
        titre = f"✏️ Projet modifié - {projet.nom}"
        message = f"Le projet '{projet.nom}' a été modifié par {utilisateur.nom}"
        
        if champs_modifies:
            message += f" - {', '.join(champs_modifies)}"
        
        # Notifier la direction
        direction_users = Utilisateur.objects.filter(role='direction')
        for user in direction_users:
            if user != utilisateur:
                NotificationService.creer_notification(
                    utilisateur=user,
                    titre=titre,
                    message=message,
                    type_notif='info',
                    lien_action=f"/app/projets/{projet.id}",
                    entite_id=projet.id,
                    entite_type='projet',
                    projet=projet
                )
        
        # Notifier le chef de projet (si différent)
        if projet.chef_projet and projet.chef_projet != utilisateur:
            NotificationService.creer_notification(
                utilisateur=projet.chef_projet,
                titre=titre,
                message=message,
                type_notif='info',
                lien_action=f"/app/projets/{projet.id}",
                entite_id=projet.id,
                entite_type='projet',
                projet=projet
            )
    
    @staticmethod
    def notifier_suppression_projet(projet, utilisateur):
        """Notification lors de la suppression d'un projet"""
        titre = f"🗑️ Projet supprimé - {projet.nom}"
        message = f"Le projet '{projet.nom}' a été supprimé par {utilisateur.nom}"
        
        # Notifier la direction
        direction_users = Utilisateur.objects.filter(role='direction')
        for user in direction_users:
            if user != utilisateur:
                NotificationService.creer_notification(
                    utilisateur=user,
                    titre=titre,
                    message=message,
                    type_notif='attention',
                    entite_id=projet.id,
                    entite_type='projet',
                    projet=projet
                )
    
    @staticmethod
    def notifier_fin_projet(projet):
        """Notification quand un projet est terminé"""
        titre = f"🏆 Projet terminé - {projet.nom}"
        message = f"Le projet '{projet.nom}' est maintenant terminé avec 100% d'avancement"
        
        # Notifier la direction
        direction_users = Utilisateur.objects.filter(role='direction')
        for user in direction_users:
            NotificationService.creer_notification(
                utilisateur=user,
                titre=titre,
                message=message,
                type_notif='succes',
                lien_action=f"/app/projets/{projet.id}",
                entite_id=projet.id,
                entite_type='projet',
                projet=projet
            )
        
        # Notifier le chef de projet
        if projet.chef_projet:
            NotificationService.creer_notification(
                utilisateur=projet.chef_projet,
                titre=titre,
                message=message,
                type_notif='succes',
                lien_action=f"/app/projets/{projet.id}",
                entite_id=projet.id,
                entite_type='projet',
                projet=projet
            )
     
    @staticmethod
    def notifier_nouveau_commentaire_document(document, utilisateur, commentaire, rating=None):
        """Notification lors d'un nouveau commentaire sur un document"""
        titre = f"💬 Nouveau commentaire - {document.projet.nom}"
        message = f"{utilisateur.nom} a commenté le document '{document.nom}': {commentaire[:50]}..."
        
        if rating:
            message += f" (Note: {rating}/5)"
        
        # Destinataires
        destinataires = set()
        
        # Chef de projet
        if document.projet.chef_projet and document.projet.chef_projet != utilisateur:
            destinataires.add(document.projet.chef_projet)
        
        # Direction
        from ..models import Utilisateur
        direction_users = Utilisateur.objects.filter(role='direction')
        for user in direction_users:
            if user != utilisateur:
                destinataires.add(user)
        
        # Si l'utilisateur est un client, notifier aussi les consultants
        if utilisateur.role == 'client':
            consultants = Utilisateur.objects.filter(role='consultant')
            for consultant in consultants:
                if consultant != utilisateur:
                    destinataires.add(consultant)
        
        # Créer les notifications
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
    
    @staticmethod
    def notifier_nouveau_document(document, utilisateur):
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
        from ..models import Utilisateur
        direction_users = Utilisateur.objects.filter(role='direction')
        for user in direction_users:
            if user != utilisateur:
                destinataires.add(user)
        
        # Si c'est un livrable, notifier aussi le client
        if document.type_fichier == 'livrable' and document.projet.client:
            if document.projet.client != utilisateur:
                destinataires.add(document.projet.client)
        
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
    
    @staticmethod
    def notifier_modification_document(document, utilisateur, ancien_nom):
        """Notification lors de la modification d'un document"""
        titre = f"✏️ Document modifié - {document.projet.nom}"
        message = f"{utilisateur.nom} a modifié '{document.nom}' (anciennement '{ancien_nom}')"
        
        destinataires = set()
        
        if document.projet.chef_projet and document.projet.chef_projet != utilisateur:
            destinataires.add(document.projet.chef_projet)
        
        from ..models import Utilisateur
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
    
    @staticmethod
    def notifier_suppression_document(document, utilisateur):
        """Notification lors de la suppression d'un document"""
        titre = f"🗑️ Document supprimé - {document.projet.nom}"
        message = f"{utilisateur.nom} a supprimé le document '{document.nom}'"
        
        destinataires = set()
        
        if document.projet.chef_projet and document.projet.chef_projet != utilisateur:
            destinataires.add(document.projet.chef_projet)
        
        from ..models import Utilisateur
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