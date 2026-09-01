import json
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from apps.usuarios.decorators import requiere_autenticacion, requiere_rol
from .models import Categoria, Producto


# ========== CARTA DIGITAL (público) ==========

@require_http_methods(["GET"])
def carta_digital(request):
    """Devuelve el menú público agrupado por categoría, solo productos disponibles."""

    # Info básica del negocio
    try:
        from apps.facturacion.models import Configuracion
        config = Configuracion.objects.first()
        nombre_negocio = config.nombre_empresa if (config and config.nombre_empresa) else 'karuAPP'
        info_empresa = {
            'nombre': f"Restaurante - {nombre_negocio}",
            'logo': None,
        }
    except Exception:
        info_empresa = {'nombre': 'Restaurante - karuAPP', 'logo': None}

    def serializar_producto(p):
        imagen_url = None
        if p.imagen:
            raw = str(p.imagen).strip()
            if raw.startswith('http'):
                imagen_url = raw
            elif raw.startswith('/media/'):
                imagen_url = raw          # ya tiene el prefijo correcto
            elif raw:
                imagen_url = '/media/' + raw.lstrip('/')
        if not imagen_url and p.imagen_archivo:
            try:
                imagen_url = p.imagen_archivo.url
            except Exception:
                pass
        return {
            'id': p.id,
            'nombre': p.nombre,
            'descripcion': p.descripcion or '',
            'ingredientes': p.ingredientes or '',
            'notas': p.notas or '',
            'precio': int(p.precio),
            'imagen': imagen_url,
            'variantes': p.variantes or [],
        }

    data = []

    # Productos con categoría
    categorias = Categoria.objects.prefetch_related('productos').order_by('orden', 'nombre')
    for cat in categorias:
        productos = cat.productos.filter(disponible=True)
        if not productos.exists():
            continue
        data.append({
            'id': cat.id,
            'nombre': cat.nombre,
            'icono': cat.icono,
            'productos': [serializar_producto(p) for p in productos],
        })

    # Productos SIN categoría (cat=None)
    sin_cat = Producto.objects.filter(disponible=True, categoria__isnull=True)
    if sin_cat.exists():
        data.append({
            'id': 0,
            'nombre': 'Otros',
            'icono': 'restaurant_menu',
            'productos': [serializar_producto(p) for p in sin_cat],
        })

    return JsonResponse({'success': True, 'empresa': info_empresa, 'categorias': data})


# ========== CATEGORÍAS ==========

@require_http_methods(["GET"])
def lista_categorias(request):
    """Lista todas las categorías"""
    categorias = Categoria.objects.all().order_by('orden', 'nombre')
    data = [{
        'id': c.id,
        'nombre': c.nombre,
        'icono': c.icono,
        'orden': c.orden
    } for c in categorias]
    return JsonResponse({'success': True, 'categorias': data})


@csrf_exempt
@require_http_methods(["POST"])
@requiere_autenticacion
def crear_categoria(request):
    """Crea una nueva categoría"""
    try:
        data = json.loads(request.body)
        nombre = data.get('nombre')
        icono = data.get('icono', 'category')
        orden = data.get('orden', 0)
        
        if not nombre:
            return JsonResponse({
                'success': False,
                'error': 'El nombre es requerido'
            }, status=400)
        
        categoria = Categoria.objects.create(
            nombre=nombre,
            icono=icono,
            orden=orden
        )
        
        return JsonResponse({
            'success': True,
            'categoria': {
                'id': categoria.id,
                'nombre': categoria.nombre,
                'icono': categoria.icono,
                'orden': categoria.orden
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["PUT"])
@requiere_autenticacion
def modificar_categoria(request, pk):
    """Modifica una categoría"""
    try:
        data = json.loads(request.body)
        try:
            categoria = Categoria.objects.get(pk=pk)
        except Categoria.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Categoría no encontrada'
            }, status=404)
        
        nombre = data.get('nombre')
        icono = data.get('icono')
        orden = data.get('orden')
        
        if nombre:
            categoria.nombre = nombre
        if icono:
            categoria.icono = icono
        if orden is not None:
            categoria.orden = orden
        
        categoria.save()
        
        return JsonResponse({
            'success': True,
            'categoria': {
                'id': categoria.id,
                'nombre': categoria.nombre,
                'icono': categoria.icono,
                'orden': categoria.orden
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
@requiere_autenticacion
def eliminar_categoria(request, pk):
    """Elimina una categoría"""
    try:
        categoria = Categoria.objects.get(pk=pk)
        categoria.delete()
        return JsonResponse({'success': True})
    except Categoria.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Categoría no encontrada'
        }, status=404)


# ========== PRODUCTOS ==========

@require_http_methods(["GET"])
def lista_productos(request):
    """Lista todos los productos"""
    categoria_id = request.GET.get('categoria_id')
    
    productos = Producto.objects.select_related('categoria').all()
    
    if categoria_id and categoria_id != '0':
        productos = productos.filter(categoria_id=categoria_id)
    
    data = []
    for p in productos:
        imagen_url = None
        if p.imagen:
            if str(p.imagen).startswith('http'):
                imagen_url = str(p.imagen)
            elif str(p.imagen).startswith('/media/'):
                imagen_url = str(p.imagen)
            else:
                imagen_url = '/media/' + str(p.imagen)
        
        imagen_archivo_url = None
        if p.imagen_archivo:
            try:
                imagen_archivo_url = p.imagen_archivo.url
            except Exception:
                pass
        
        data.append({
            'id': p.id,
            'nombre': p.nombre,
            'descripcion': p.descripcion,
            'ingredientes': p.ingredientes,
            'notas': p.notas,
            'precio': str(p.precio),
            'categoria_id': p.categoria_id,
            'categoria_nombre': p.categoria.nombre if p.categoria else None,
            'disponible': p.disponible,
            'iva': p.iva,
            'imagen': imagen_url or imagen_archivo_url,
            'imagen_archivo': imagen_archivo_url,
            'variantes': p.variantes
        })
    
    return JsonResponse({'success': True, 'productos': data})


@csrf_exempt
@require_http_methods(["POST"])
@requiere_autenticacion
def crear_producto(request):
    """Crea un nuevo producto"""
    try:
        data = json.loads(request.body)
        nombre = data.get('nombre')
        precio = data.get('precio', 0)
        descripcion = data.get('descripcion', '')
        ingredientes = data.get('ingredientes', '')
        notas = data.get('notas', '')
        categoria_id = data.get('categoria_id')
        disponible = data.get('disponible', True)
        variantes = data.get('variantes')
        
        if not nombre or not precio:
            return JsonResponse({
                'success': False,
                'error': 'Nombre y precio son requeridos'
            }, status=400)
        
        producto = Producto.objects.create(
            nombre=nombre,
            descripcion=descripcion,
            ingredientes=ingredientes,
            notas=notas,
            precio=precio,
            categoria_id=categoria_id,
            disponible=disponible,
            iva=data.get('iva', 10),
            variantes=variantes,
            imagen=data.get('imagen', '')
        )
        
        # Auto-crear Inventario si no existe
        from apps.inventario.models import Inventario
        Inventario.objects.get_or_create(
            producto=producto,
            defaults={'stock_actual': 100, 'stock_minimo': 5, 'unidad_medida': 'und', 'precio_costo': 0}
        )
        
        return JsonResponse({
            'success': True,
            'producto': {
                'id': producto.id,
                'nombre': producto.nombre,
                'precio': str(producto.precio),
                'disponible': producto.disponible
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["PUT"])
@requiere_autenticacion
def modificar_producto(request, pk):
    """Modifica un producto"""
    try:
        data = json.loads(request.body)
        try:
            producto = Producto.objects.get(pk=pk)
        except Producto.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Producto no encontrado'
            }, status=404)
        
        producto.nombre = data.get('nombre', producto.nombre)
        producto.descripcion = data.get('descripcion', producto.descripcion)
        producto.ingredientes = data.get('ingredientes', producto.ingredientes)
        producto.notas = data.get('notas', producto.notas)
        producto.precio = data.get('precio', producto.precio)
        producto.categoria_id = data.get('categoria_id', producto.categoria_id)
        producto.disponible = data.get('disponible', producto.disponible)
        producto.iva = data.get('iva', producto.iva)
        producto.imagen = data.get('imagen', producto.imagen)
        producto.variantes = data.get('variantes', producto.variantes)
        
        producto.save()
        
        return JsonResponse({
            'success': True,
            'producto': {
                'id': producto.id,
                'nombre': producto.nombre,
                'precio': str(producto.precio),
                'disponible': producto.disponible
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["PUT"])
@requiere_autenticacion
def modificar_carta(request, pk):
    """Actualiza el contenido de un producto para la carta digital
    (descripción, ingredientes, notas y disponibilidad)."""
    try:
        data = json.loads(request.body)
        try:
            producto = Producto.objects.get(pk=pk)
        except Producto.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Producto no encontrado'
            }, status=404)

        if 'descripcion' in data:
            v = data.get('descripcion')
            producto.descripcion = v if isinstance(v, str) else str(v or '')
        if 'ingredientes' in data:
            v = data.get('ingredientes')
            producto.ingredientes = v if isinstance(v, str) else str(v or '')
        if 'notas' in data:
            v = data.get('notas')
            producto.notas = v if isinstance(v, str) else str(v or '')
        if 'disponible' in data:
            producto.disponible = bool(data.get('disponible'))

        producto.save()

        # Notificar a la carta digital abierta para que se actualice en tiempo real
        try:
            from pipperfood.socket_events import emit_carta_actualizada
            emit_carta_actualizada()
        except Exception:
            pass

        return JsonResponse({
            'success': True,
            'producto': {
                'id': producto.id,
                'descripcion': producto.descripcion or '',
                'ingredientes': producto.ingredientes or '',
                'notas': producto.notas or '',
                'disponible': producto.disponible,
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
@requiere_autenticacion
def eliminar_producto(request, pk):
    """Elimina un producto"""
    try:
        producto = Producto.objects.get(pk=pk)
        producto.delete()
        return JsonResponse({'success': True})
    except Producto.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Producto no encontrado'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al eliminar: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
@requiere_rol('administrador')
def limpiar_productos(request):
    """Elimina todos los productos, inventario y movimientos"""
    try:
        from apps.inventario.models import Inventario, MovimientoInventario
        
        MovimientoInventario.objects.all().delete()
        Inventario.objects.all().delete()
        Producto.objects.all().delete()
        Categoria.objects.all().delete()
        
        return JsonResponse({'success': True, 'message': 'Todos los productos e inventario fueron eliminados'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
@requiere_autenticacion
def subir_imagen(request):
    """Sube una imagen para un producto"""
    try:
        if 'imagen' not in request.FILES:
            return JsonResponse({'success': False, 'error': 'No se envió ninguna imagen'}, status=400)
        
        archivo = request.FILES['imagen']
        
        from django.core.files.storage import default_storage
        from django.core.files.base import ContentFile
        import uuid
        
        ext = archivo.name.split('.')[-1] if '.' in archivo.name else 'jpg'
        nombre_archivo = f'productos/{uuid.uuid4().hex}.{ext}'
        ruta_guardada = default_storage.save(nombre_archivo, ContentFile(archivo.read()))
        
        url = f'{settings.MEDIA_URL}{ruta_guardada}'
        
        return JsonResponse({
            'success': True,
            'url': url,
            'ruta': ruta_guardada
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
@requiere_autenticacion
def toggle_producto(request, pk):
    """Alterna la disponibilidad de un producto"""
    try:
        producto = Producto.objects.get(pk=pk)
        producto.disponible = not producto.disponible
        producto.save()
        
        # Notificar a la carta digital abierta para que se actualice en tiempo real
        try:
            from pipperfood.socket_events import emit_carta_actualizada
            emit_carta_actualizada()
        except Exception:
            pass
        
        return JsonResponse({
            'success': True,
            'producto': {
                'id': producto.id,
                'disponible': producto.disponible
            }
        })
    except Producto.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Producto no encontrado'
        }, status=404)