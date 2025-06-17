from flask import Blueprint, render_template, request, make_response, flash, redirect, url_for, send_file, current_app
from flask_login import login_required, current_user
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from config.database import db_config
from models import Pedido, PedidoProducto, Producto, Cliente
from datetime import datetime, date, timedelta
import io
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment

reportes_bp = Blueprint('reportes', __name__, url_prefix='/reportes')

def get_current_year():
    """Obtener el año actual para el footer"""
    return datetime.now().year

@reportes_bp.route('/pedidos')
def reporte_pedidos():
    """Reporte de pedidos con filtros y paginación"""
    db = db_config.get_session()
    try:
        # Parámetros de filtro
        fecha_desde = request.args.get('fecha_desde', '')
        fecha_hasta = request.args.get('fecha_hasta', '')
        estado = request.args.get('estado', '')
        cliente_id = request.args.get('cliente_id', '')
        page = int(request.args.get('page', 1))
        per_page = 20

        # Query base
        query = db.query(Pedido)

        # Aplicar filtros
        if fecha_desde:
            try:
                fecha_desde_dt = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
                query = query.filter(func.date(Pedido.fecha_creacion) >= fecha_desde_dt)
            except ValueError:
                flash('Fecha desde inválida', 'error')

        if fecha_hasta:
            try:
                fecha_hasta_dt = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
                query = query.filter(func.date(Pedido.fecha_creacion) <= fecha_hasta_dt)
            except ValueError:
                flash('Fecha hasta inválida', 'error')

        if estado:
            query = query.filter(Pedido.estado_pedido_general == estado)

        if cliente_id and cliente_id != 'todos':
            try:
                cliente_id_int = int(cliente_id)
                query = query.filter(Pedido.cliente_id == cliente_id_int)
            except ValueError:
                flash('ID de cliente inválido', 'error')

        # Ordenar por fecha de creación descendente
        query = query.order_by(desc(Pedido.fecha_creacion))

        # Paginación
        total = query.count()
        pedidos = query.offset((page - 1) * per_page).limit(per_page).all()

        # Crear objeto de paginación manual
        class Pagination:
            def __init__(self, page, per_page, total):
                self.page = page
                self.per_page = per_page
                self.total = total
                self.pages = (total + per_page - 1) // per_page
                self.has_prev = page > 1
                self.prev_num = page - 1 if self.has_prev else None
                self.has_next = page < self.pages
                self.next_num = page + 1 if self.has_next else None

            def iter_pages(self, left_edge=2, right_edge=2, left_current=2, right_current=3):
                last = self.pages
                for num in range(1, last + 1):
                    if num <= left_edge or \
                       (self.page - left_current - 1 < num < self.page + right_current) or \
                       num > last - right_edge:
                        yield num

        pagination = Pagination(page, per_page, total)

        # Obtener datos para filtros
        estados = db.query(Pedido.estado_pedido_general).distinct().filter(
            Pedido.estado_pedido_general.isnot(None)
        ).all()
        estados = [e[0] for e in estados if e[0]]

        clientes = db.query(Cliente).order_by(Cliente.nombre_comercial).all()

        current_year = get_current_year()
        
        return render_template('reporte_pedidos.html', 
                             pedidos=pedidos,
                             pagination=pagination,
                             estados=estados,
                             clientes=clientes,
                             current_user=current_user,
                             current_year=current_year)
    
    except Exception as e:
        flash(f'Error al generar el reporte: {str(e)}', 'error')
        return redirect(url_for('pedidos.lista'))
    finally:
        db.close()

@reportes_bp.route('/consolidado')
@reportes_bp.route('/consolidado-productos')  # Agregar ruta alternativa con guiones
def consolidado_productos():
    """Consolidado de productos pedidos agrupados por categoría con subtotales por formulación y referencia"""
    db = db_config.get_session()
    try:
        # Parámetros de filtro
        estado = request.args.get('estado', '')
        fecha_desde = request.args.get('fecha_desde', '')
        fecha_hasta = request.args.get('fecha_hasta', '')
        categoria = request.args.get('categoria', '')
        formulacion = request.args.get('formulacion', '')

        # Query base para obtener items de pedidos con información de productos e incluir comentarios
        query = db.query(
            PedidoProducto.cantidad,
            PedidoProducto.peso_total_g_item,
            PedidoProducto.comentarios_item,
            Producto.referencia_de_producto,
            Producto.formulacion_grupo,
            Producto.categoria_linea,
            Pedido.id.label('pedido_id')
        ).join(
            Producto, PedidoProducto.producto_id == Producto.id
        ).join(
            Pedido, PedidoProducto.pedido_id == Pedido.id
        )

        # Aplicar filtros
        if estado:
            query = query.filter(Pedido.estado_pedido_general == estado)

        if fecha_desde:
            try:
                fecha_desde_dt = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
                query = query.filter(func.date(Pedido.fecha_creacion) >= fecha_desde_dt)
            except ValueError:
                flash('Fecha desde inválida', 'error')

        if fecha_hasta:
            try:
                fecha_hasta_dt = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
                query = query.filter(func.date(Pedido.fecha_creacion) <= fecha_hasta_dt)
            except ValueError:
                flash('Fecha hasta inválida', 'error')

        if categoria:
            query = query.filter(Producto.categoria_linea.ilike(f'%{categoria}%'))

        if formulacion:
            query = query.filter(Producto.formulacion_grupo.ilike(f'%{formulacion}%'))

        # Obtener resultados
        resultados = query.all()

        # Agrupar por categoría, luego por formulación, luego por referencia de producto
        resultados_agrupados = {}
        subtotales_referencia = {}
        subtotales_formulacion = {}
        totales_categoria = {}
        total_cantidad = 0
        total_peso = 0

        for resultado in resultados:
            categoria_key = resultado.categoria_linea or 'Sin Categoría'
            formulacion_key = resultado.formulacion_grupo or 'Sin Formulación'
            referencia_key = resultado.referencia_de_producto or 'Sin Referencia'
            
            # Inicializar estructura de categoría si no existe
            if categoria_key not in resultados_agrupados:
                resultados_agrupados[categoria_key] = {}
                totales_categoria[categoria_key] = {'cantidad': 0, 'peso': 0}
            
            # Inicializar estructura de formulación dentro de la categoría
            if formulacion_key not in resultados_agrupados[categoria_key]:
                resultados_agrupados[categoria_key][formulacion_key] = {}
                subtotales_formulacion[f"{categoria_key}|{formulacion_key}"] = {'cantidad': 0, 'peso': 0}

            # Inicializar estructura de referencia dentro de la formulación
            if referencia_key not in resultados_agrupados[categoria_key][formulacion_key]:
                resultados_agrupados[categoria_key][formulacion_key][referencia_key] = []
                subtotales_referencia[f"{categoria_key}|{formulacion_key}|{referencia_key}"] = {'cantidad': 0, 'peso': 0}

            # Crear objeto de item
            item = {
                'categoria': resultado.categoria_linea,
                'formulacion': resultado.formulacion_grupo,
                'referencia': resultado.referencia_de_producto,
                'comentarios': resultado.comentarios_item or '',
                'pedido_id': resultado.pedido_id,
                'total_cantidad': resultado.cantidad or 0,
                'total_peso': resultado.peso_total_g_item or 0
            }

            resultados_agrupados[categoria_key][formulacion_key][referencia_key].append(item)
            
            # Actualizar subtotales de referencia
            subtotal_ref_key = f"{categoria_key}|{formulacion_key}|{referencia_key}"
            subtotales_referencia[subtotal_ref_key]['cantidad'] += item['total_cantidad']
            subtotales_referencia[subtotal_ref_key]['peso'] += item['total_peso']
            
            # Actualizar subtotales de formulación
            subtotal_form_key = f"{categoria_key}|{formulacion_key}"
            subtotales_formulacion[subtotal_form_key]['cantidad'] += item['total_cantidad']
            subtotales_formulacion[subtotal_form_key]['peso'] += item['total_peso']
            
            # Actualizar totales de categoría
            totales_categoria[categoria_key]['cantidad'] += item['total_cantidad']
            totales_categoria[categoria_key]['peso'] += item['total_peso']
            
            # Actualizar totales generales
            total_cantidad += item['total_cantidad']
            total_peso += item['total_peso']

        # Obtener datos para filtros
        estados = db.query(Pedido.estado_pedido_general).distinct().filter(
            Pedido.estado_pedido_general.isnot(None)
        ).all()
        estados = [e[0] for e in estados if e[0]]

        categorias = db.query(Producto.categoria_linea).distinct().filter(
            Producto.categoria_linea.isnot(None)
        ).all()
        categorias = [c[0] for c in categorias if c[0]]

        formulaciones = db.query(Producto.formulacion_grupo).distinct().filter(
            Producto.formulacion_grupo.isnot(None)
        ).all()
        formulaciones = [f[0] for f in formulaciones if f[0]]

        # Crear objeto de filtros para pasar a la plantilla
        filtros = {
            'estado': estado,
            'fecha_desde': fecha_desde,
            'fecha_hasta': fecha_hasta,
            'categoria': categoria,
            'formulacion': formulacion
        }

        current_year = get_current_year()

        return render_template('consolidado_productos.html',
                             resultados_agrupados=resultados_agrupados,
                             subtotales_referencia=subtotales_referencia,
                             subtotales_formulacion=subtotales_formulacion,
                             totales_categoria=totales_categoria,
                             total_cantidad=total_cantidad,
                             total_peso=total_peso,
                             estados=estados,
                             categorias=categorias,
                             formulaciones=formulaciones,
                             filtros=filtros,
                             current_user=current_user,
                             current_year=current_year)

    except Exception as e:
        flash(f'Error al generar el consolidado: {str(e)}', 'error')
        return redirect(url_for('pedidos.lista'))
    finally:
        db.close()

@reportes_bp.route('/exportar-pedidos-excel')
def exportar_pedidos_excel():
    """Exportar reporte de pedidos a Excel con estructura jerárquica por cliente"""
    db = db_config.get_session()
    try:
        # Aplicar los mismos filtros que en el reporte
        fecha_desde = request.args.get('fecha_desde', '')
        fecha_hasta = request.args.get('fecha_hasta', '')
        estado = request.args.get('estado', '')
        cliente_id = request.args.get('cliente_id', '')

        # Query base con join para obtener información completa
        query = db.query(Pedido).join(
            PedidoProducto, Pedido.id == PedidoProducto.pedido_id
        ).join(
            Producto, PedidoProducto.producto_id == Producto.id
        ).outerjoin(
            Cliente, Pedido.cliente_id == Cliente.id
        )

        # Aplicar filtros
        if fecha_desde:
            try:
                fecha_desde_dt = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
                query = query.filter(func.date(Pedido.fecha_creacion) >= fecha_desde_dt)
            except ValueError:
                pass

        if fecha_hasta:
            try:
                fecha_hasta_dt = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
                query = query.filter(func.date(Pedido.fecha_creacion) <= fecha_hasta_dt)
            except ValueError:
                pass

        if estado:
            query = query.filter(Pedido.estado_pedido_general == estado)

        if cliente_id and cliente_id != 'todos':
            try:
                cliente_id_int = int(cliente_id)
                query = query.filter(Pedido.cliente_id == cliente_id_int)
            except ValueError:
                pass

        # Obtener pedidos únicos y ordenarlos
        pedidos = query.distinct().order_by(desc(Pedido.fecha_creacion)).all()

        # Agrupar pedidos por cliente
        pedidos_por_cliente = {}
        for pedido in pedidos:
            cliente_key = (
                pedido.cliente_asociado.nombre_comercial if pedido.cliente_asociado 
                else pedido.nombre_cliente_ingresado or 'Cliente no registrado'
            )
            
            if cliente_key not in pedidos_por_cliente:
                pedidos_por_cliente[cliente_key] = []
            
            pedidos_por_cliente[cliente_key].append(pedido)

        # Crear libro de Excel
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Reporte de Pedidos"

        # Estilos
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        cliente_font = Font(bold=True, color="FFFFFF", size=14)
        cliente_fill = PatternFill(start_color="0066CC", end_color="0066CC", fill_type="solid")  # Azul
        pedido_font = Font(bold=True, color="000000")
        pedido_fill = PatternFill(start_color="B3D9FF", end_color="B3D9FF", fill_type="solid")  # Azul claro
        center_alignment = Alignment(horizontal="center")
        left_alignment = Alignment(horizontal="left")

        # Encabezados
        headers = [
            "Código Producto", "Referencia", "Cantidad", "Comentarios", "Dirección", "Horarios"
        ]
        
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = center_alignment

        # Datos con estructura jerárquica
        row = 2
        
        if pedidos_por_cliente:
            for cliente_nombre, pedidos_cliente in pedidos_por_cliente.items():
                # Nivel 1: Cliente (azul, texto grande)
                cliente_cell = ws.cell(row=row, column=1, value=f"👤 {cliente_nombre}")
                cliente_cell.font = cliente_font
                cliente_cell.fill = cliente_fill
                cliente_cell.alignment = left_alignment
                ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=6)
                row += 1
                
                for pedido in pedidos_cliente:
                    # Nivel 2: Productos del Pedido dentro de Cliente (azul claro)
                    pedido_info = f"📦 Pedido #{pedido.id} - {pedido.fecha_creacion.strftime('%d/%m/%Y')} - Estado: {pedido.estado_pedido_general}"
                    pedido_cell = ws.cell(row=row, column=1, value=pedido_info)
                    pedido_cell.font = pedido_font
                    pedido_cell.fill = pedido_fill
                    pedido_cell.alignment = left_alignment
                    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=6)
                    row += 1
                    
                    # Consolidar productos iguales dentro del mismo pedido
                    productos_consolidados = {}
                    
                    for item in pedido.items:
                        if item.producto_asociado:
                            producto_key = (item.producto_asociado.codigo, item.producto_asociado.referencia_de_producto)
                            
                            if producto_key not in productos_consolidados:
                                productos_consolidados[producto_key] = {
                                    'codigo': item.producto_asociado.codigo,
                                    'referencia': item.producto_asociado.referencia_de_producto,
                                    'cantidad_total': 0,
                                    'comentarios': []
                                }
                            
                            # Sumar cantidad
                            productos_consolidados[producto_key]['cantidad_total'] += item.cantidad or 0
                            
                            # Recopilar comentarios únicos
                            if item.comentarios_item and item.comentarios_item.strip():
                                if item.comentarios_item not in productos_consolidados[producto_key]['comentarios']:
                                    productos_consolidados[producto_key]['comentarios'].append(item.comentarios_item)
                    
                    # Nivel 3: Items consolidados de productos
                    for producto_key, producto_data in productos_consolidados.items():
                        # Código del producto
                        ws.cell(row=row, column=1, value=producto_data['codigo'])
                        
                        # Referencia del producto
                        ws.cell(row=row, column=2, value=producto_data['referencia'])
                        
                        # Cantidad total consolidada
                        ws.cell(row=row, column=3, value=f"{producto_data['cantidad_total']} unidades")
                        
                        # Comentarios consolidados
                        comentarios_texto = "; ".join(producto_data['comentarios']) if producto_data['comentarios'] else 'Sin comentarios'
                        ws.cell(row=row, column=4, value=comentarios_texto)
                        
                        # Dirección
                        direccion_completa = []
                        if pedido.direccion_entrega:
                            direccion_completa.append(pedido.direccion_entrega)
                        if pedido.ciudad_entrega:
                            direccion_completa.append(pedido.ciudad_entrega)
                        if pedido.departamento_entrega:
                            direccion_completa.append(pedido.departamento_entrega)
                        
                        direccion = ", ".join(direccion_completa) if direccion_completa else 'Sin dirección especificada'
                        ws.cell(row=row, column=5, value=direccion)
                        
                        # Horarios
                        horario = pedido.despacho_horario_atencion if pedido.despacho_horario_atencion else 'Sin horario especificado'
                        ws.cell(row=row, column=6, value=horario)
                        
                        row += 1
                    
                    # Línea en blanco para separar pedidos
                    row += 1
                
                # Línea en blanco adicional para separar clientes
                row += 1
        else:
            # No hay resultados
            no_results_cell = ws.cell(row=row, column=1, value="No se encontraron pedidos con los filtros seleccionados")
            ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=6)
            no_results_cell.alignment = center_alignment

        # Ajustar ancho de columnas
        column_widths = [18, 35, 15, 30, 40, 25]  # Anchos específicos para cada columna
        for i, width in enumerate(column_widths, 1):
            column_letter = openpyxl.utils.get_column_letter(i)
            ws.column_dimensions[column_letter].width = width

        # Crear respuesta
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)

        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        response.headers['Content-Disposition'] = f'attachment; filename=reporte_pedidos_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        
        return response

    except Exception as e:
        flash(f'Error al exportar: {str(e)}', 'error')
        return redirect(url_for('reportes.reporte_pedidos'))
    finally:
        db.close()

@reportes_bp.route('/exportar-consolidado-excel')
def exportar_consolidado_excel():
    """Exportar consolidado de productos a Excel agrupado por categoría con subtotales por formulación"""
    db = db_config.get_session()
    try:
        # Aplicar los mismos filtros que en el consolidado
        estado = request.args.get('estado', '')
        fecha_desde = request.args.get('fecha_desde', '')
        fecha_hasta = request.args.get('fecha_hasta', '')
        categoria = request.args.get('categoria', '')
        formulacion = request.args.get('formulacion', '')

        # Query base (misma lógica que en consolidado_productos)
        query = db.query(
            PedidoProducto.cantidad,
            PedidoProducto.peso_total_g_item,
            PedidoProducto.comentarios_item,
            Producto.referencia_de_producto,
            Producto.formulacion_grupo,
            Producto.categoria_linea,
            Pedido.id.label('pedido_id')
        ).join(
            Producto, PedidoProducto.producto_id == Producto.id
        ).join(
            Pedido, PedidoProducto.pedido_id == Pedido.id
        )

        # Aplicar filtros
        if estado:
            query = query.filter(Pedido.estado_pedido_general == estado)
        if fecha_desde:
            try:
                fecha_desde_dt = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
                query = query.filter(func.date(Pedido.fecha_creacion) >= fecha_desde_dt)
            except ValueError:
                pass
        if fecha_hasta:
            try:
                fecha_hasta_dt = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
                query = query.filter(func.date(Pedido.fecha_creacion) <= fecha_hasta_dt)
            except ValueError:
                pass
        if categoria:
            query = query.filter(Producto.categoria_linea.ilike(f'%{categoria}%'))
        if formulacion:
            query = query.filter(Producto.formulacion_grupo.ilike(f'%{formulacion}%'))

        resultados = query.all()

        # Agrupar primero por categoría, luego por formulación, luego por referencia de producto (misma lógica que en consolidado_productos)
        resultados_agrupados = {}
        subtotales_referencia = {}
        subtotales_formulacion = {}
        totales_categoria = {}
        total_cantidad = 0
        total_peso = 0

        for resultado in resultados:
            categoria_key = resultado.categoria_linea or 'Sin Categoría'
            formulacion_key = resultado.formulacion_grupo or 'Sin Formulación'
            referencia_key = resultado.referencia_de_producto or 'Sin Referencia'
            
            # Inicializar estructura de categoría si no existe
            if categoria_key not in resultados_agrupados:
                resultados_agrupados[categoria_key] = {}
                totales_categoria[categoria_key] = {'cantidad': 0, 'peso': 0}
            
            # Inicializar estructura de formulación dentro de la categoría
            if formulacion_key not in resultados_agrupados[categoria_key]:
                resultados_agrupados[categoria_key][formulacion_key] = {}
                subtotales_formulacion[f"{categoria_key}|{formulacion_key}"] = {'cantidad': 0, 'peso': 0}

            # Inicializar estructura de referencia dentro de la formulación
            if referencia_key not in resultados_agrupados[categoria_key][formulacion_key]:
                resultados_agrupados[categoria_key][formulacion_key][referencia_key] = []
                subtotales_referencia[f"{categoria_key}|{formulacion_key}|{referencia_key}"] = {'cantidad': 0, 'peso': 0}

            # Crear objeto de item
            item = {
                'categoria': resultado.categoria_linea,
                'formulacion': resultado.formulacion_grupo,
                'referencia': resultado.referencia_de_producto,
                'comentarios': resultado.comentarios_item or '',
                'pedido_id': resultado.pedido_id,
                'total_cantidad': resultado.cantidad or 0,
                'total_peso': resultado.peso_total_g_item or 0
            }

            resultados_agrupados[categoria_key][formulacion_key][referencia_key].append(item)
            
            # Actualizar subtotales de referencia
            subtotal_ref_key = f"{categoria_key}|{formulacion_key}|{referencia_key}"
            subtotales_referencia[subtotal_ref_key]['cantidad'] += item['total_cantidad']
            subtotales_referencia[subtotal_ref_key]['peso'] += item['total_peso']
            
            # Actualizar subtotales de formulación
            subtotal_form_key = f"{categoria_key}|{formulacion_key}"
            subtotales_formulacion[subtotal_form_key]['cantidad'] += item['total_cantidad']
            subtotales_formulacion[subtotal_form_key]['peso'] += item['total_peso']
            
            # Actualizar totales de categoría
            totales_categoria[categoria_key]['cantidad'] += item['total_cantidad']
            totales_categoria[categoria_key]['peso'] += item['total_peso']
            
            # Actualizar totales generales
            total_cantidad += item['total_cantidad']
            total_peso += item['total_peso']

        # Crear libro de Excel
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Consolidado de Productos"

        # Estilos
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        categoria_font = Font(bold=True, color="000000", size=14)
        categoria_fill = PatternFill(start_color="0066CC", end_color="0066CC", fill_type="solid")  # Azul
        formulacion_font = Font(bold=True, color="000000")
        formulacion_fill = PatternFill(start_color="D1ECF1", end_color="D1ECF1", fill_type="solid")  # Azul claro
        subtotal_font = Font(bold=True, color="000000")
        subtotal_fill = PatternFill(start_color="FFF3CD", end_color="FFF3CD", fill_type="solid")  # Amarillo claro
        total_categoria_font = Font(bold=True, color="000000")
        total_categoria_fill = PatternFill(start_color="E9ECEF", end_color="E9ECEF", fill_type="solid")  # Gris claro
        total_font = Font(bold=True, color="FFFFFF")
        total_fill = PatternFill(start_color="343A40", end_color="343A40", fill_type="solid")  # Gris oscuro
        center_alignment = Alignment(horizontal="center")
        right_alignment = Alignment(horizontal="right")

        # Encabezados
        headers = [
            "Formulación", "Referencia de Producto", "Comentarios",
            "# Pedido", "Cantidad", "Peso Total (g)"
        ]
        
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = center_alignment

        # Datos con estructura igual a la tabla HTML
        row = 2
        
        if resultados_agrupados:
            for categoria_key, formulaciones in resultados_agrupados.items():
                # Encabezado de Categoría
                cell = ws.cell(row=row, column=1, value=f"🏷️ {categoria_key}")
                cell.font = categoria_font
                cell.fill = categoria_fill
                ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=6)
                row += 1
                
                for formulacion_key, referencias in formulaciones.items():
                    # Encabezado de Formulación
                    cell = ws.cell(row=row, column=1, value=f"    🧪 {formulacion_key}")
                    cell.font = formulacion_font
                    cell.fill = formulacion_fill
                    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=6)
                    row += 1
                    
                    for referencia_key, items in referencias.items():
                        # Encabezado de Referencia de Producto
                        referencia_font = Font(bold=True, color="000000")
                        referencia_fill = PatternFill(start_color="E8F5E8", end_color="E8F5E8", fill_type="solid")  # Verde claro
                        
                        cell = ws.cell(row=row, column=1, value=f"      📦 {referencia_key}")
                        cell.font = referencia_font
                        cell.fill = referencia_fill
                        ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=6)
                        row += 1
                        
                        # Items de la referencia
                        for item in items:
                            ws.cell(row=row, column=1, value=item['formulacion'] or '-')
                            ws.cell(row=row, column=2, value=item['referencia'] or '-')
                            ws.cell(row=row, column=3, value=item['comentarios'] or '-')
                            ws.cell(row=row, column=4, value=item['pedido_id'])
                            
                            # Cantidad y peso con formato numérico y alineación derecha
                            cantidad_cell = ws.cell(row=row, column=5, value=round(item['total_cantidad'], 2))
                            cantidad_cell.alignment = right_alignment
                            peso_cell = ws.cell(row=row, column=6, value=round(item['total_peso'], 2))
                            peso_cell.alignment = right_alignment
                            
                            row += 1
                        
                        # Subtotal de Referencia
                        subtotal_ref_font = Font(bold=True, color="000000")
                        subtotal_ref_fill = PatternFill(start_color="D4F1D4", end_color="D4F1D4", fill_type="solid")  # Verde
                        
                        subtotal_ref_cell = ws.cell(row=row, column=4, value=f"📦 Subtotal {referencia_key}:")
                        subtotal_ref_cell.font = subtotal_ref_font
                        subtotal_ref_cell.fill = subtotal_ref_fill
                        subtotal_ref_cell.alignment = right_alignment
                        
                        # Merge las primeras 4 columnas para el texto del subtotal de referencia
                        ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=4)
                        
                        # Subtotal referencia cantidad
                        subtotal_ref_key = f"{categoria_key}|{formulacion_key}|{referencia_key}"
                        subtotal_ref_cantidad_cell = ws.cell(row=row, column=5, value=round(subtotales_referencia[subtotal_ref_key]['cantidad'], 2))
                        subtotal_ref_cantidad_cell.font = subtotal_ref_font
                        subtotal_ref_cantidad_cell.fill = subtotal_ref_fill
                        subtotal_ref_cantidad_cell.alignment = right_alignment
                        
                        # Subtotal referencia peso
                        subtotal_ref_peso_cell = ws.cell(row=row, column=6, value=round(subtotales_referencia[subtotal_ref_key]['peso'], 2))
                        subtotal_ref_peso_cell.font = subtotal_ref_font
                        subtotal_ref_peso_cell.fill = subtotal_ref_fill
                        subtotal_ref_peso_cell.alignment = right_alignment
                        
                        row += 1
                    
                    # Subtotal de Formulación
                    subtotal_cell = ws.cell(row=row, column=4, value=f"🧮 Subtotal {formulacion_key}:")
                    subtotal_cell.font = subtotal_font
                    subtotal_cell.fill = subtotal_fill
                    subtotal_cell.alignment = right_alignment
                    
                    # Merge las primeras 4 columnas para el texto del subtotal
                    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=4)
                    
                    # Subtotal cantidad
                    subtotal_key = f"{categoria_key}|{formulacion_key}"
                    subtotal_cantidad_cell = ws.cell(row=row, column=5, value=round(subtotales_formulacion[subtotal_key]['cantidad'], 2))
                    subtotal_cantidad_cell.font = subtotal_font
                    subtotal_cantidad_cell.fill = subtotal_fill
                    subtotal_cantidad_cell.alignment = right_alignment
                    
                    # Subtotal peso
                    subtotal_peso_cell = ws.cell(row=row, column=6, value=round(subtotales_formulacion[subtotal_key]['peso'], 2))
                    subtotal_peso_cell.font = subtotal_font
                    subtotal_peso_cell.fill = subtotal_fill
                    subtotal_peso_cell.alignment = right_alignment
                    
                    row += 1
                
                # Total de Categoría
                total_cat_cell = ws.cell(row=row, column=4, value=f"🏷️ Total {categoria_key}:")
                total_cat_cell.font = total_categoria_font
                total_cat_cell.fill = total_categoria_fill
                total_cat_cell.alignment = right_alignment
                
                # Merge las primeras 4 columnas para el texto del total de categoría
                ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=4)
                
                # Total categoría cantidad
                total_cat_cantidad_cell = ws.cell(row=row, column=5, value=round(totales_categoria[categoria_key]['cantidad'], 2))
                total_cat_cantidad_cell.font = total_categoria_font
                total_cat_cantidad_cell.fill = total_categoria_fill
                total_cat_cantidad_cell.alignment = right_alignment
                
                # Total categoría peso
                total_cat_peso_cell = ws.cell(row=row, column=6, value=round(totales_categoria[categoria_key]['peso'], 2))
                total_cat_peso_cell.font = total_categoria_font
                total_cat_peso_cell.fill = total_categoria_fill
                total_cat_peso_cell.alignment = right_alignment
                
                row += 1
                
                # Línea en blanco para separar categorías
                row += 1
        else:
            # No hay resultados
            no_results_cell = ws.cell(row=row, column=1, value="No se encontraron resultados con los filtros seleccionados")
            ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=6)
            no_results_cell.alignment = center_alignment
            row += 1

        # Total General
        total_cell = ws.cell(row=row, column=4, value="🔢 TOTALES GENERALES:")
        total_cell.font = total_font
        total_cell.fill = total_fill
        total_cell.alignment = right_alignment
        
        # Merge las primeras 4 columnas para el texto del total
        ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=4)
        
        # Total cantidad
        total_cantidad_cell = ws.cell(row=row, column=5, value=round(total_cantidad, 2))
        total_cantidad_cell.font = total_font
        total_cantidad_cell.fill = total_fill
        total_cantidad_cell.alignment = right_alignment
        
        # Total peso
        total_peso_cell = ws.cell(row=row, column=6, value=round(total_peso, 2))
        total_peso_cell.font = total_font
        total_peso_cell.fill = total_fill
        total_peso_cell.alignment = right_alignment

        # Ajustar ancho de columnas
        column_widths = [25, 30, 25, 12, 12, 15]  # Anchos específicos para cada columna
        for i, width in enumerate(column_widths, 1):
            column_letter = openpyxl.utils.get_column_letter(i)
            ws.column_dimensions[column_letter].width = width

        # Crear respuesta
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)

        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        response.headers['Content-Disposition'] = f'attachment; filename=consolidado_productos_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        
        return response

    except Exception as e:
        flash(f'Error al exportar: {str(e)}', 'error')
        return redirect(url_for('reportes.consolidado_productos'))
    finally:
        db.close()