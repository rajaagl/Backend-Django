from django.db import models

class utilisateur(models.Model):
    nom = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    motDePasse = models.CharField(max_length=100)
    telephone = models.CharField(max_length=20)
    photoProfil = models.ImageField(upload_to='photos_profils/', null=True, blank=True)
    dateCreation = models.DateTimeField(auto_now_add=True)
    dernierConnexion = models.DateTimeField(auto_now=True)
    actif = models.BooleanField(default=True)

    class Meta :
           abstract = False

class direction(utilisateur):
   niveauAcces = models.CharField(max_length=50)

class chefProjet(utilisateur):
    specialite = models.CharField(max_length=100)
    certifications = models.CharField(max_length=200)
    
class client(utilisateur):
    societe = models.CharField(max_length=100)
    secteurActivite = models.CharField(max_length=100)
    numeroSiret = models.CharField(max_length=20)

class partenaire(utilisateur):
    typePartenaire = models.CharField(max_length=50)
    contrat = models.CharField(max_length=200)
    dateDebutPartenariat = models.DateField()

class consultant(utilisateur):
    competences = models.CharField(max_length=200)
    disponibilite = models.BooleanField(default=True)
    chargeTravail = models.IntegerField(default=0)
    chefProjet = models.ForeignKey(chefProjet, on_delete=models.CASCADE)

class projet(models.Model):
    nom = models.CharField(max_length=100)
    description = models.TextField()
    objectsif = models.CharField(max_length=100)
    dateDebut = models.DateField()
    dateFinPrevue = models.DateField()
    dateFinReelle = models.DateField(null=True, blank=True)
    budget = models.DecimalField(max_digits=10, decimal_places=2)
    statut = models.CharField(max_length=50)
    avancementGlobale = models.DecimalField(max_digits=5, decimal_places=2)
    client = models.ForeignKey(client, on_delete=models.CASCADE)
    chefProjet = models.ForeignKey(chefProjet, on_delete=models.CASCADE)
    partenaires = models.ManyToManyField(partenaire)
    
class tache(models.Model):
    titre = models.CharField(max_length=100)
    description = models.TextField()
    priorite = models.CharField(max_length=50)
    avancement = models.IntegerField()
    dateDebut = models.DateField()
    dateFinPrevue = models.DateField()
    dateFinReelle = models.DateField(null=True, blank=True)
    statut = models.CharField(max_length=50)
    avancement = models.DecimalField(max_digits=5, decimal_places=2)
    projet = models.ForeignKey(projet, on_delete=models.CASCADE)
    consultant = models.ForeignKey(consultant, on_delete=models.CASCADE)
    
class sousTache(models.Model):
    titre = models.CharField(max_length=100)
    statut = models.CharField(max_length=50)
    avancement = models.DecimalField(max_digits=5, decimal_places=2)
    dateEcheance = models.DateField()
    tache = models.ForeignKey(tache, on_delete=models.CASCADE)

class commentaire(models.Model):
    contenu = models.TextField()
    datePublication = models.DateTimeField(auto_now_add=True)
    utilisateur = models.ForeignKey(utilisateur, on_delete=models.CASCADE)
    tache = models.ForeignKey(tache, on_delete=models.CASCADE)

class document(models.Model):
    nom = models.CharField(max_length=100)
    chemin = models.FileField(upload_to='documents/')
    version = models.CharField(max_length=20)
    taille = models.IntegerField()
    typeFichier = models.CharField(max_length=50)
    dateUpload = models.DateTimeField(auto_now_add=True)
    projet = models.ForeignKey(projet, on_delete=models.CASCADE)

class ressource(models.Model):
    type = models.CharField(max_length=50)
    nom = models.CharField(max_length=100)
    coutUnitaire = models.DecimalField(max_digits=10, decimal_places=2)
    disponible= models.BooleanField(default=True)
    projet = models.ManyToManyField(projet)

class notification(models.Model):
    type=models.CharField(max_length=50)
    titre=models.CharField(max_length=50)
    message=models.CharField()
    lue=models.BooleanField()
    dateEnvoi=models.DateTimeField()
    utilisateur = models.ForeignKey(utilisateur, on_delete=models.CASCADE)

class kpi(models.Model):
    nom =models.CharField(max_length=50)
    valeurCible =models.FloatField()
    valeurActuelle = models.FloatField()
    unite = models.CharField(max_length=255)
    seuilAlerte = models.FloatField()
    projet = models.ForeignKey(projet, on_delete=models.CASCADE)

class conversation(models.Model):
    titre = models.CharField()
    dateCreation = models.DateTimeField(auto_now_add=True)
    dateDerniereMessage = models.DateTimeField(auto_now_add=True)
    projet = models.ForeignKey(projet, on_delete=models.CASCADE)

class message (models.Model):
    contenu = models.CharField()
    dateEnvoi = models.DateTimeField(auto_now_add=True)
    lu = models.BooleanField(False)
    typeMessage = models.CharField()
    conversation = models.ForeignKey(conversation,on_delete=models.CASCADE)

class budget (models.Model):
    montantTotal = models.FloatField()
    montantDepense =models.FloatField()
    montantRestant =models.FloatField()
    devise = models.CharField()
    projet = models.ForeignKey(projet, on_delete=models.CASCADE ,related_name='budgets')