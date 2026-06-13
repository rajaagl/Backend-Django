# ramaqs_management_plateforme/middleware.py

from django.http import JsonResponse
from .models import Tenant

class TenantMiddleware:
    """
    Middleware qui extrait le tenant depuis le header X-Tenant-ID
    ou depuis l'utilisateur connecté
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        tenant_id = request.headers.get('X-Tenant-ID')
        
        if tenant_id:
            try:
                import uuid
                try:
                    tenant_uuid = uuid.UUID(tenant_id)
                    request.tenant = Tenant.objects.get(id=tenant_uuid, actif=True)
                except (ValueError, TypeError):
                    request.tenant = Tenant.objects.get(slug=tenant_id, actif=True)
            except Tenant.DoesNotExist:
                request.tenant = None
        else:
            # ✅ AJOUTEZ CE BLOC : Utiliser le tenant de l'utilisateur connecté
            if request.user.is_authenticated:
                membership = request.user.memberships.first()
                if membership:
                    request.tenant = membership.tenant
                else:
                    request.tenant = None
            else:
                request.tenant = None
        
        response = self.get_response(request)
        return response
    
    def process_exception(self, request, exception):
        """Gestion des erreurs liées au tenant"""
        if hasattr(request, 'tenant') and request.tenant is None:
            return JsonResponse(
                {'error': 'Tenant invalide ou inexistant'},
                status=404
            )
        return None