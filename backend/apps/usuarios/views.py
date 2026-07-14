import json
import random
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import Usuario, Rol


# ==================== CRUD USUARIOS ====================

@csrf_exempt
@require_http_methods(["GET"])
def lista_usuarios(request):
    """Lista todos los usuarios"""
    incluir_inactivos = request.GET.get('incluir_inactivos') == 'true'
    only_activos = request.GET.get('only_activos') == 'true'
    
    if only_activos:
        usuarios = Usuario.objects.filter(activo=True).order_by('nombre')
    elif incluir_inactivos:
        usuarios = Usuario.objects.all().order_by('nombre')
    else:
        usuarios = Usuario.objects.filter(activo=True).order_by('nombre')
    
    data = [{
        'id': u.id,
        'nombre': u.nombre,
        'rol': u.rol,
        'telefono': u.telefono,
        'email': u.email,
        'activo': u.activo,
        'ultimo_acceso': u.ultimo_acceso.isoformat() if u.ultimo_acceso else None,
        'created_at': u.created_at.isoformat() if u.created_at else None,
    } for u in usuarios]
    
    return JsonResponse({'success': True, 'usuarios': data})


def generar_pin_unico():
    """Genera un PIN de 4 dígitos no usado"""
    for _ in range(100):
        pin = f"{random.randint(0, 9999):04d}"
        if not Usuario.objects.filter(pin=pin).exists():
            return pin
    return None


@csrf_exempt
@require_http_methods(["POST"])
def crear_usuario(request):
    """Crea un nuevo usuario"""
    try:
        data = json.loads(request.body)
        nombre = data.get('nombre', '').strip()
        pin = data.get('pin', '').strip()
        rol = data.get('rol', 'mesero')
        telefono = data.get('telefono', '')
        email = data.get('email', '')
        
        if not nombre:
            return JsonResponse({
                'success': False,
                'error': 'El nombre es requerido'
            }, status=400)
        
        if pin:
            if len(pin) != 4 or not pin.isdigit():
                return JsonResponse({
                    'success': False,
                    'error': 'El PIN debe tener 4 dígitos numericos'
                }, status=400)
            if Usuario.objects.filter(pin=pin).exists():
                return JsonResponse({
                    'success': False,
                    'error': 'Este PIN ya está en uso'
                }, status=400)
        else:
            pin = generar_pin_unico()
            if not pin:
                return JsonResponse({
                    'success': False,
                    'error': 'No se pudo generar un PIN unico'
                }, status=500)
        
        usuario = Usuario.objects.create(
            nombre=nombre,
            pin=pin,
            rol=rol,
            telefono=telefono,
            email=email,
        )
        
        return JsonResponse({
            'success': True,
            'usuario': {
                'id': usuario.id,
                'nombre': usuario.nombre,
                'rol': usuario.rol,
                'pin': usuario.pin,
                'telefono': usuario.telefono,
                'email': usuario.email,
                'activo': usuario.activo,
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["PUT"])
def modificar_usuario(request, pk):
    """Modifica un usuario"""
    try:
        data = json.loads(request.body)
        try:
            usuario = Usuario.objects.get(pk=pk)
        except Usuario.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Usuario no encontrado'
            }, status=404)
        
        nombre = data.get('nombre')
        pin = data.get('pin')
        rol = data.get('rol')
        telefono = data.get('telefono')
        email = data.get('email')
        activo = data.get('activo')
        
        if nombre:
            usuario.nombre = nombre.strip()
        if pin:
            if len(pin) == 4 and pin.isdigit():
                if pin != usuario.pin and Usuario.objects.filter(pin=pin).exists():
                    return JsonResponse({
                        'success': False,
                        'error': 'Este PIN ya está en uso'
                    }, status=400)
                usuario.pin = pin
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'El PIN debe tener 4 digitos numericos'
                }, status=400)
        if rol:
            usuario.rol = rol
        if telefono is not None:
            usuario.telefono = telefono
        if email is not None:
            usuario.email = email
        if activo is not None:
            usuario.activo = activo
        
        usuario.save()
        
        return JsonResponse({
            'success': True,
            'usuario': {
                'id': usuario.id,
                'nombre': usuario.nombre,
                'rol': usuario.rol,
                'pin': usuario.pin,
                'telefono': usuario.telefono,
                'email': usuario.email,
                'activo': usuario.activo,
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
def eliminar_usuario(request, pk):
    """Desactiva un usuario"""
    try:
        usuario = Usuario.objects.get(pk=pk)
        usuario.activo = False
        usuario.save()
        return JsonResponse({'success': True, 'mensaje': 'Usuario desactivado'})
    except Usuario.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Usuario no encontrado'
        }, status=404)


@csrf_exempt
@require_http_methods(["POST"])
def activar_usuario(request, pk):
    """Activa un usuario"""
    try:
        usuario = Usuario.objects.get(pk=pk)
        usuario.activo = True
        usuario.save()
        return JsonResponse({'success': True, 'mensaje': 'Usuario activado'})
    except Usuario.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Usuario no encontrado'
        }, status=404)


@csrf_exempt
@require_http_methods(["POST"])
def reestablecer_pin(request, pk):
    """Reestablece el PIN de un usuario"""
    try:
        data = json.loads(request.body)
        nuevo_pin = data.get('pin', '').strip()
        
        try:
            usuario = Usuario.objects.get(pk=pk)
        except Usuario.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Usuario no encontrado'
            }, status=404)
        
        if nuevo_pin:
            if len(nuevo_pin) != 4 or not nuevo_pin.isdigit():
                return JsonResponse({
                    'success': False,
                    'error': 'El PIN debe tener 4 digitos numericos'
                }, status=400)
            if Usuario.objects.filter(pin=nuevo_pin).exclude(pk=pk).exists():
                return JsonResponse({
                    'success': False,
                    'error': 'Este PIN ya está en uso'
                }, status=400)
        else:
            nuevo_pin = generar_pin_unico()
            if not nuevo_pin:
                return JsonResponse({
                    'success': False,
                    'error': 'No se pudo generar un PIN unico'
                }, status=500)
        
        usuario.pin = nuevo_pin
        usuario.save(update_fields=['pin'])
        
        return JsonResponse({
            'success': True,
            'mensaje': 'PIN reestablecido',
            'pin': nuevo_pin
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
def estadisticas_usuarios(request):
    """Estadisticas de usuarios para el dashboard de funcionarios"""
    total = Usuario.objects.count()
    activos = Usuario.objects.filter(activo=True).count()
    inactivos = total - activos
    
    por_rol = {}
    for rol, _ in Rol.choices:
        por_rol[rol] = Usuario.objects.filter(rol=rol).count()
    
    return JsonResponse({
        'success': True,
        'estadisticas': {
            'total': total,
            'activos': activos,
            'inactivos': inactivos,
            'por_rol': por_rol,
        }
    })