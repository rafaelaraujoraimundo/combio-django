from django.db.models.signals import post_migrate
from django.dispatch import receiver
from global_permissions.models import GlobalPermission


@receiver(post_migrate)
def create_global_permissions(sender, **kwargs):
    if sender.name == 'menu':
        # Crie as permissões desejadas
        dashboard_ti = GlobalPermission.objects.get_or_create(
            codename='dashboard_ti',
            name='Acesso dashboard_ti'
        )
        dashboard_controladoria = GlobalPermission.objects.get_or_create(
            codename='dashboard_controladoria',
            name='Acesso dashboard_controladoria'
        )
