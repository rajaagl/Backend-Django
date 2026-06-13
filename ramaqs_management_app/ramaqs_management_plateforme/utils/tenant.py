# utils/tenant.py
from django.utils.deprecation import MiddlewareMixin

class TenantMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Récupérer le tenant depuis le header X-Tenant-ID
        tenant_slug = request.headers.get('X-Tenant-ID')
        if tenant_slug:
            from ..models import Tenant
            try:
                request.tenant = Tenant.objects.get(slug=tenant_slug)
            except Tenant.DoesNotExist:
                request.tenant = None
        else:
            request.tenant = None

def get_current_tenant(request=None):
    """Récupère le tenant actuel"""
    if request and hasattr(request, 'tenant'):
        return request.tenant
    from ..models import Tenant
    return Tenant.objects.first()