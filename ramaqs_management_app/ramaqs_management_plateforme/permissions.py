from rest_framework import permissions
from .models import RoleChoices

class IsTenantAuthenticated(permissions.BasePermission):
    """Vérifie que la requête a un tenant valide"""
    
    def has_permission(self, request, _view):
        return hasattr(request, 'tenant') and request.tenant is not None


class IsTenantMember(permissions.BasePermission):
    """Vérifie que l'utilisateur est membre du tenant"""
    
    def has_permission(self, request, _view):
        if not hasattr(request, 'tenant') or not request.tenant:
            return False
        if not request.user.is_authenticated:
            return False
        role = request.user.get_role_in_tenant(request.tenant)
        return role is not None


class IsTenantAdmin(permissions.BasePermission):
    """Vérifie que l'utilisateur est admin du tenant (Super Admin ou Direction)"""
    
    def has_permission(self, request, _view):
        if not hasattr(request, 'tenant') or not request.tenant:
            return False
        if not request.user.is_authenticated:
            return False
        role = request.user.get_role_in_tenant(request.tenant)
        return role in [RoleChoices.SUPER_ADMIN, RoleChoices.DIRECTION]


class IsSuperAdmin(permissions.BasePermission):
    """Vérifie que l'utilisateur est Super Admin"""
    
    def has_permission(self, request, _view):
        return request.user.is_authenticated and request.user.is_super_admin()


class IsDirection(permissions.BasePermission):
    """Vérifie que l'utilisateur est Direction RAMAQS"""
    
    def has_permission(self, request, _view):
        if not hasattr(request, 'tenant') or not request.tenant:
            return False
        if not request.user.is_authenticated:
            return False
        role = request.user.get_role_in_tenant(request.tenant)
        return role == RoleChoices.DIRECTION


class IsChefProjet(permissions.BasePermission):
    """Vérifie que l'utilisateur est Chef de projet"""
    
    def has_permission(self, request, _view):
        if not hasattr(request, 'tenant') or not request.tenant:
            return False
        if not request.user.is_authenticated:
            return False
        role = request.user.get_role_in_tenant(request.tenant)
        return role == RoleChoices.CHEF_PROJET


class IsConsultant(permissions.BasePermission):
    """Vérifie que l'utilisateur est Consultant"""
    
    def has_permission(self, request, _view):
        if not hasattr(request, 'tenant') or not request.tenant:
            return False
        if not request.user.is_authenticated:
            return False
        role = request.user.get_role_in_tenant(request.tenant)
        return role == RoleChoices.CONSULTANT


class IsClient(permissions.BasePermission):
    """Vérifie que l'utilisateur est Client"""
    
    def has_permission(self, request, _view):
        if not hasattr(request, 'tenant') or not request.tenant:
            return False
        if not request.user.is_authenticated:
            return False
        role = request.user.get_role_in_tenant(request.tenant)
        return role == RoleChoices.CLIENT


class IsPartenaire(permissions.BasePermission):
    """Vérifie que l'utilisateur est Partenaire"""
    
    def has_permission(self, request, _view):
        if not hasattr(request, 'tenant') or not request.tenant:
            return False
        if not request.user.is_authenticated:
            return False
        role = request.user.get_role_in_tenant(request.tenant)
        return role == RoleChoices.PARTENAIRE