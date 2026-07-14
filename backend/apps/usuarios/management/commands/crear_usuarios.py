from django.core.management.base import BaseCommand
from apps.usuarios.models import Usuario


class Command(BaseCommand):
    help = 'Crea los usuarios por defecto del sistema'

    def handle(self, *args, **options):
        usuarios = [
            {'nombre': 'Admin', 'pin': '0000', 'rol': 'administrador'},
            {'nombre': 'mesero1', 'pin': '1111', 'rol': 'mesero'},
            {'nombre': 'mesero2', 'pin': '2222', 'rol': 'mesero'},
            {'nombre': 'cocina', 'pin': '3333', 'rol': 'cocina'},
        ]

        for u in usuarios:
            if Usuario.objects.filter(nombre=u['nombre']).exists():
                self.stdout.write(f"  - {u['nombre']} ya existe, omitiendo")
                continue

            Usuario.objects.create(nombre=u['nombre'], pin=u['pin'], rol=u['rol'])
            self.stdout.write(f"  + {u['nombre']} creado (PIN: {u['pin']})")

        self.stdout.write(self.style.SUCCESS('Usuarios por defecto creados exitosamente'))
