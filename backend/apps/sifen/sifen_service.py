import os
import logging
from datetime import datetime, date
from decimal import Decimal
from typing import Optional

from django.conf import settings

logger = logging.getLogger(__name__)

try:
    from pysifen.de.bindings.v150.fe_v141 import (
        RDe, TDe, TgCopeDe, TgDtim, TgDaGoc, TgOpeCom, TgEmis,
        TgCamFe, TgCamCond, TgCamItem, TgValorItem, TgCamIva,
        TgDtipDe, TgTotSub, TgCamGen, TgDatRec, TgCamFuFd,
        TgPagCont, TgActEco, TdDesTipEmi, TdDesTiDe,
        TiIndPres, TiCondOpe, TiTimp, TiTipTra, TiTiPago,
        TcUniMed, TiAfecIva, CMondT, PaisType,
        TDepartamentos, TDesDepartamento,
    )
    from pysifen.transmissao import TransmissaoDE
    from pysifen.transmissao.config import PRODUCCION, TEST
    SIFEN_AVAILABLE = True
except ImportError as e:
    SIFEN_AVAILABLE = False
    logger.warning(f'SIFEN library import error: {e}. SIFEN features disabled.')


def get_ambiente(ambiente_str: str) -> int:
    if ambiente_str == 'produccion':
        return PRODUCCION
    return TEST


def generar_de01(pedido, config, cliente_ruc='44444444-7', cliente_nombre='CONSUMIDOR FINAL'):
    if not SIFEN_AVAILABLE:
        raise ImportError('SIFEN library not installed. Run: pip install sifen[sign,transmissao]')

    now = datetime.now()
    ruc_sin_dv = config.ruc.split('-')[0] if '-' in config.ruc else config.ruc
    dv = config.ruc.split('-')[-1] if '-' in config.ruc else '0'
    timbrado = config.timbrado_numero or '12345678'
    establecimiento = config.establecimiento or '001'
    punto_exp = config.punto_expedicion or '001'
    # Usar el número de factura del timbrado si está disponible
    num_factura = pedido.get('numero_factura', '')
    if num_factura and '-' in num_factura:
        num_doc = num_factura.split('-')[-1].zfill(7)
    else:
        num_doc = str(pedido.get('numero_orden', '1')).zfill(7)

    total_bruto = Decimal('0')
    total_iva = Decimal('0')
    total_gral = Decimal('0')
    tasa_iva_val = int(config.tasa_iva or 10)
    items = []

    for idx, item in enumerate(pedido.get('items', []), start=1):
        cantidad = Decimal(str(item.get('cantidad', 1)))
        precio = Decimal(str(item.get('precio', 0)))
        total_item = cantidad * precio
        iva_item = total_item * Decimal(str(tasa_iva_val)) / Decimal('100')
        base_grav = total_item - iva_item

        desc_item = item.get('producto_nombre') or item.get('nombre') or ''
        if item.get('variante'):
            desc_item += f' - {item["variante"]}'

        g_item = TgCamItem(
            dCodInt=str(item.get('producto_id', '')),
            dDesProSer=desc_item[:100],
            cUniMed=TcUniMed.VALUE_77,
            dDesUniMed='UNI',
            dCantProSer=cantidad,
            gValorItem=TgValorItem(
                dPUniProSer=precio,
                dDescItem=Decimal('0'),
                dTotOpeItem=total_item,
                dTotOpeGs=total_item,
            ),
            gCamIVA=TgCamIva(
                iAfecIVA=TiAfecIva.VALUE_1,
                dDesAfecIVA='Gravado IVA',
                dPropIVA=100,
                dTasaIVA=tasa_iva_val,
                dBasGravIVA=base_grav,
                dLiqIVAItem=iva_item,
            ),
        )
        items.append(g_item)
        total_bruto += total_item
        total_iva += iva_item
        total_gral += total_item

    # Timestamp for Id generation
    id_ts = now.strftime('%Y%m%d%H%M%S%f')[:19]
    de_id = f'{ruc_sin_dv}{establecimiento}{punto_exp}{num_doc}{id_ts}'

    fec_firma = now.strftime('%Y-%m-%dT%H:%M:%S')
    fec_emision = now.strftime('%Y-%m-%dT%H:%M:%S')

    # Build RDe
    rde = RDe(
        dVerFor='150',
        DE=TDe(
            Id=de_id,
            dDVId=dv,
            dFecFirma=fec_firma,
            gOpeDE=TgCopeDe(
                iTipEmi='1',
                dDesTipEmi='Normal',
                dCodSeg='000000001',
            ),
            gTimb=TgDtim(
                iTiDE='1',
                dDesTiDE='Factura electr\u00f3nica',
                dNumTim=timbrado,
                dEst=establecimiento,
                dPunExp=punto_exp,
                dNumDoc=num_doc,
                dFeIniT=(config.fecha_inicio or date.today()).strftime('%Y-%m-%d'),
                dFeFinT=(config.fecha_vencimiento or date.today()).strftime('%Y-%m-%d'),
            ),
            gDatGralOpe=TgDaGoc(
                dFeEmiDE=fec_emision,
                gOpeCom=TgOpeCom(
                    iTipTra=TiTipTra.VALUE_1,
                    dDesTipTra='Venta de mercader\u00eda',
                    iTImp=TiTimp.VALUE_1,
                    dDesTImp='IVA',
                    cMoneOpe=CMondT.PYG,
                    dDesMoneOpe='Guaran\u00ed',
                ),
                gEmis=TgEmis(
                    dRucEm=ruc_sin_dv,
                    dDVEmi=dv,
                    iTipCont='1',
                    cTipReg='1',
                    dNomEmi=config.nombre_empresa[:60],
                    dNomFanEmi=config.nombre_empresa[:30],
                    dDirEmi=config.cDirEmi or config.direccion or '',
                    dNumCas=config.dNumCas or 0,
                    cDepEmi=getattr(TDepartamentos, f'VALUE_{config.cDepEmi}', TDepartamentos.VALUE_1),
                    dDesDepEmi=config.dDesDepEmi or 'CAPITAL',
                    cCiuEmi=config.cCiuEmi or '1',
                    dDesCiuEmi=config.dDesCiuEmi or 'ASUNCION (DISTRITO)',
                    dTelEmi=config.telefono or '',
                    dEmailE=config.dEmailE or '',
                    gActEco=[TgActEco(
                        cActEco=config.gActEco_codigo or '47111',
                        dDesActEco=(config.gActEco_descripcion or 'Venta al por menor')[:100],
                    )],
                ),
                gDatRec=TgDatRec(
                    iNatRec='1',
                    iTiOpe='1',
                    cPaisRec=PaisType.PRY,
                    dDesPaisRe='Paraguay',
                    iTiContRec='1',
                    dNomRec=cliente_nombre[:60] if cliente_nombre else 'CONSUMIDOR FINAL',
                    dRucRec=cliente_ruc.split('-')[0] if '-' in cliente_ruc else cliente_ruc,
                    dDVRec=cliente_ruc.split('-')[-1] if '-' in cliente_ruc else '0',
                    dDirRec='',
                    dTelRec='',
                ),
            ),
            gDtipDE=TgDtipDe(
                gCamFE=TgCamFe(
                    iIndPres=TiIndPres.VALUE_1,
                    dDesIndPres='Operaci\u00f3n presencial',
                ),
                gCamCond=TgCamCond(
                    iCondOpe=TiCondOpe.VALUE_1,
                    dDCondOpe='Contado',
                    gPaConEIni=[
                        TgPagCont(
                            iTiPago=TiTiPago.VALUE_1,
                            dDesTiPag='Efectivo',
                            dMonTiPag=total_gral,
                            cMoneTiPag=CMondT.PYG,
                            dDMoneTiPag='Guaran\u00ed',
                        ),
                    ],
                ),
                gCamItem=items,
            ),
            gTotSub=TgTotSub(
                dSub10=total_bruto,
                dTotOpe=total_bruto,
                dTotDesc=Decimal('0'),
                dPorcDescTotal=Decimal('0'),
                dDescTotal=Decimal('0'),
                dAnticipo=Decimal('0'),
                dRedon=Decimal('0'),
                dTotGralOpe=total_gral,
                dIVA10=total_iva,
                dBaseGrav10=total_bruto - total_iva,
                dTBasGraIVA=total_bruto - total_iva,
                dTotIVA=total_iva,
                dTotalGs=total_gral,
            ),
            gCamGen=TgCamGen(),
        ),
        gCamFuFD=TgCamFuFd(
            dCarQR='',
        ),
    )

    return rde


def transmitir_sincrono(rde, cert_data: bytes, password: str, ambiente: str):
    """Envía un DE-01 a SIFEN de forma síncrona.

    Args:
        rde: instancia de RDe (documento electrónico)
        cert_data: bytes del certificado PKCS12
        password: PIN del certificado
        ambiente: 'test' o 'produccion'

    Returns:
        RRetEnviDe con el resultado (dProtAut contiene el CDC)
    """
    if not SIFEN_AVAILABLE:
        raise ImportError('SIFEN library not installed. Run: pip install sifen[sign,transmissao]')
    amb = get_ambiente(ambiente)
    trans = TransmissaoDE(ambiente=amb, pkcs12_data=cert_data, pkcs12_password=password)
    result = trans.enviar_de(rde, sign=True)
    return result


def transmitir_lote(lista_rde: list, cert_data: bytes, password: str, ambiente: str):
    """Envía un lote de DEs a SIFEN (asíncrono, hasta 50 DEs)."""
    if not SIFEN_AVAILABLE:
        raise ImportError('SIFEN library not installed')
    amb = get_ambiente(ambiente)
    trans = TransmissaoDE(ambiente=amb, pkcs12_data=cert_data, pkcs12_password=password)
    result = trans.enviar_lote(lista_rde, sign=True)
    return result


def consultar_por_cdc(cdc: str, cert_data: bytes, password: str, ambiente: str):
    if not SIFEN_AVAILABLE:
        raise ImportError('SIFEN library not installed')
    amb = get_ambiente(ambiente)
    from pysifen.transmissao import ConsultaSIFEN
    consulta = ConsultaSIFEN(ambiente=amb, pkcs12_data=cert_data, pkcs12_password=password)
    result = consulta.consulta_de(cdc)
    return result


def extraer_cdc(result) -> str:
    """Extrae el CDC del resultado de enviar_de."""
    try:
        if hasattr(result, 'dProtAut'):
            return result.dProtAut or ''
        if hasattr(result, 'cdc'):
            return result.cdc
        return ''
    except Exception:
        return ''


def extraer_estado(result) -> str:
    """Extrae el estado del resultado."""
    try:
        if hasattr(result, 'dEstRes'):
            return str(result.dEstRes)
        return ''
    except Exception:
        return ''


def extraer_mensaje(result) -> str:
    """Extrae el mensaje del resultado."""
    try:
        if hasattr(result, 'gResProc') and result.gResProc:
            return result.gResProc[0].dMsgRes if isinstance(result.gResProc, list) else result.gResProc.dMsgRes
        return ''
    except Exception:
        return ''


def extraer_codigo_resultado(result) -> str:
    """Extrae el código de resultado."""
    try:
        if hasattr(result, 'gResProc') and result.gResProc:
            return result.gResProc[0].dCodRes if isinstance(result.gResProc, list) else result.gResProc.dCodRes
        return ''
    except Exception:
        return ''
