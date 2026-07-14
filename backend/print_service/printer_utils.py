import win32print

PRINTER_TYPES = ['yp', 'yichi', 'thermal', 'pos', 'receipt', 'ticket', 'bematech', 'daruma', 'elgin', 'ftx', 'tdr', '58mm', '80mm']

def listar_impresoras():
    impresoras = []
    for name in win32print.EnumPrinters(2):
        nombre = name[2]
        es_termica = any(marca in nombre.lower() for marca in PRINTER_TYPES)
        impresoras.append({
            'nombre': nombre,
            'termica': es_termica
        })
    return impresoras

def detectar_impresora_termica():
    for p in listar_impresoras():
        if p['termica']:
            return p['nombre']
    impresoras = listar_impresoras()
    if impresoras:
        return impresoras[0]['nombre']
    return None

def imprimir_texto(nombre_impresora, texto):
    handle = win32print.OpenPrinter(nombre_impresora)
    try:
        job_id = win32print.StartDocPrinter(handle, 1, ("Ticket", None, "RAW"))
        win32print.StartPagePrinter(handle)
        if isinstance(texto, str):
            datos = texto.encode('cp1252', errors='replace')
        else:
            datos = texto
        win32print.WritePrinter(handle, datos)
        win32print.EndPagePrinter(handle)
        win32print.EndDocPrinter(handle)
        return True
    except Exception as e:
        raise e
    finally:
        win32print.ClosePrinter(handle)
