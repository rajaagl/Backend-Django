from django.db import models

class TenantQuerySet(models.QuerySet):
    def filter_by_tenant(self, tenant):
        if tenant:
            return self.filter(tenant=tenant)
        return self.none()

class TenantManager(models.Manager):
    def get_queryset(self):
        return TenantQuerySet(self.model, using=self._db)
    
    def filter_by_tenant(self, tenant):
        return self.get_queryset().filter_by_tenant(tenant)