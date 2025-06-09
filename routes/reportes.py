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
    """Consolidado de productos pedidos agrupados por formulación"""
    db = db_config.get_session()
    try:
        # Parámetros de filtro
        estado = request.args.get('estado', '')
        fecha_desde = request.args.get('fecha_desde', '')
        fecha_hasta = request.args.get('fecha_hasta', '')
        formulacion = request.args.get('formulacion', '')

        # Query base para obtener items de pedidos con información de productos y clientes
        query = db.query(
            PedidoProducto.cantidad,
            PedidoProducto.peso_total_g_item,
            Producto.referencia_de_producto,
            Producto.formulacion_grupo,
            Producto.categoria_linea,
            Cliente.nombre_comercial.label('cliente_nombre'),
            Cliente.numero_identificacion.label('cliente_nit'),
            Pedido.id.label('pedido_id')
        ).join(
            Producto, PedidoProducto.producto_id == Producto.id
        ).join(
            Pedido, PedidoProducto.pedido_id == Pedido.id
        ).outerjoin(
            Cliente, Pedido.cliente_id == Cliente.id
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

        if formulacion:
            query = query.filter(Producto.formulacion_grupo.ilike(f'%{formulacion}%'))

        # Obtener resultados
        resultados = query.all()

        # Agrupar por formulación
        resultados_agrupados = {}
        subtotales_formulacion = {}
        total_cantidad = 0
        total_peso = 0

        for resultado in resultados:
            formulacion_key = resultado.formulacion_grupo or 'Sin Formulación'
            
            if formulacion_key not in resultados_agrupados:
                resultados_agrupados[formulacion_key] = []
                subtotales_formulacion[formulacion_key] = {'cantidad': 0, 'peso': 0}

            # Crear objeto de item
            item = {
                'cliente_nombre': resultado.cliente_nombre or 'Cliente no registrado',
                'cliente_nit': resultado.cliente_nit or 'N/A',
                'categoria': resultado.categoria_linea,
                'formulacion': resultado.formulacion_grupo,
                'referencia': resultado.referencia_de_producto,
                'pedido_id': resultado.pedido_id,
                'total_cantidad': resultado.cantidad or 0,
                'total_peso': resultado.peso_total_g_item or 0
            }

            resultados_agrupados[formulacion_key].append(item)
            
            # Actualizar subtotales
            subtotales_formulacion[formulacion_key]['cantidad'] += item['total_cantidad']
            subtotales_formulacion[formulacion_key]['peso'] += item['total_peso']
            
            # Actualizar totales generales
            total_cantidad += item['total_cantidad']
            total_peso += item['total_peso']

        # Obtener datos para filtros
        estados = db.query(Pedido.estado_pedido_general).distinct().filter(
            Pedido.estado_pedido_general.isnot(None)
        ).all()
        estados = [e[0] for e in estados if e[0]]

        formulaciones = db.query(Producto.formulacion_grupo).distinct().filter(
            Producto.formulacion_grupo.isnot(None)
        ).all()
        formulaciones = [f[0] for f in formulaciones if f[0]]

        # Crear objeto de filtros para pasar a la plantilla
        filtros = {
            'estado': estado,
            'fecha_desde': fecha_desde,
            'fecha_hasta': fecha_hasta,
            'formulacion': formulacion
        }

        current_year = get_current_year()

        return render_template('consolidado_productos.html',
                             resultados_agrupados=resultados_agrupados,
                             subtotales_formulacion=subtotales_formulacion,
                             total_cantidad=total_cantidad,
                             total_peso=total_peso,
                             estados=estados,
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
    """Exportar reporte de pedidos a Excel"""
    db = db_config.get_session()
    try:
        # Aplicar los mismos filtros que en el reporte
        fecha_desde = request.args.get('fecha_desde', '')
        fecha_hasta = request.args.get('fecha_hasta', '')
        estado = request.args.get('estado', '')
        cliente_id = request.args.get('cliente_id', '')

        # Query base
        query = db.query(Pedido)

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

        pedidos = query.order_by(desc(Pedido.fecha_creacion)).all()

        # Crear libro de Excel
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Reporte de Pedidos"

        # Estilos
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        center_alignment = Alignment(horizontal="center")

        # Encabezados
        headers = [
            "# Pedido", "Fecha", "Cliente", "Identificación", 
            "Productos", "Total (g)", "Estado"
        ]
        
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = center_alignment

        # Datos
        for row, pedido in enumerate(pedidos, 2):
            cliente_nombre = (pedido.cliente_asociado.nombre_comercial 
                            if pedido.cliente_asociado 
                            else pedido.nombre_cliente_ingresado or 'N/A')
            
            cliente_id_display = (pedido.cliente_asociado.numero_identificacion 
                                if pedido.cliente_asociado 
                                else pedido.numero_identificacion_cliente_ingresado or 'N/A')
            
            total_peso = sum(item.peso_total_g_item or 0 for item in pedido.items)
            
            ws.cell(row=row, column=1, value=pedido.id)
            ws.cell(row=row, column=2, value=pedido.fecha_creacion.strftime('%d/%m/%Y %H:%M'))
            ws.cell(row=row, column=3, value=cliente_nombre)
            ws.cell(row=row, column=4, value=cliente_id_display)
            ws.cell(row=row, column=5, value=f"{len(pedido.items)} producto(s)")
            ws.cell(row=row, column=6, value=total_peso)
            ws.cell(row=row, column=7, value=pedido.estado_pedido_general)

        # Ajustar ancho de columnas
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width

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
    """Exportar consolidado de productos a Excel con la misma estructura que la tabla HTML"""
    db = db_config.get_session()
    try:
        # Aplicar los mismos filtros que en el consolidado
        estado = request.args.get('estado', '')
        fecha_desde = request.args.get('fecha_desde', '')
        fecha_hasta = request.args.get('fecha_hasta', '')
        formulacion = request.args.get('formulacion', '')

        # Query base (misma lógica que en consolidado_productos)
        query = db.query(
            PedidoProducto.cantidad,
            PedidoProducto.peso_total_g_item,
            Producto.referencia_de_producto,
            Producto.formulacion_grupo,
            Producto.categoria_linea,
            Cliente.nombre_comercial.label('cliente_nombre'),
            Cliente.numero_identificacion.label('cliente_nit'),
            Pedido.id.label('pedido_id')
        ).join(
            Producto, PedidoProducto.producto_id == Producto.id
        ).join(
            Pedido, PedidoProducto.pedido_id == Pedido.id
        ).outerjoin(
            Cliente, Pedido.cliente_id == Cliente.id
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
        if formulacion:
            query = query.filter(Producto.formulacion_grupo.ilike(f'%{formulacion}%'))

        resultados = query.all()

        # Agrupar por formulación (misma lógica que en consolidado_productos)
        resultados_agrupados = {}
        subtotales_formulacion = {}
        total_cantidad = 0
        total_peso = 0

        for resultado in resultados:
            formulacion_key = resultado.formulacion_grupo or 'Sin Formulación'
            
            if formulacion_key not in resultados_agrupados:
                resultados_agrupados[formulacion_key] = []
                subtotales_formulacion[formulacion_key] = {'cantidad': 0, 'peso': 0}

            # Crear objeto de item
            item = {
                'cliente_nombre': resultado.cliente_nombre or 'Cliente no registrado',
                'cliente_nit': resultado.cliente_nit or 'N/A',
                'categoria': resultado.categoria_linea,
                'formulacion': resultado.formulacion_grupo,
                'referencia': resultado.referencia_de_producto,
                'pedido_id': resultado.pedido_id,
                'total_cantidad': resultado.cantidad or 0,
                'total_peso': resultado.peso_total_g_item or 0
            }

            resultados_agrupados[formulacion_key].append(item)
            
            # Actualizar subtotales
            subtotales_formulacion[formulacion_key]['cantidad'] += item['total_cantidad']
            subtotales_formulacion[formulacion_key]['peso'] += item['total_peso']
            
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
        formulacion_font = Font(bold=True, color="000000")
        formulacion_fill = PatternFill(start_color="D1ECF1", end_color="D1ECF1", fill_type="solid")  # Azul claro
        subtotal_font = Font(bold=True, color="000000")
        subtotal_fill = PatternFill(start_color="FFF3CD", end_color="FFF3CD", fill_type="solid")  # Amarillo claro
        total_font = Font(bold=True, color="000000")
        total_fill = PatternFill(start_color="E9ECEF", end_color="E9ECEF", fill_type="solid")  # Gris claro
        center_alignment = Alignment(horizontal="center")
        right_alignment = Alignment(horizontal="right")

        # Encabezados
        headers = [
            "Cliente", "Categoría", "Formulación", "Referencia de Producto",
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
            for formulacion_key, items in resultados_agrupados.items():
                # Encabezado de Formulación
                cell = ws.cell(row=row, column=1, value=f"🧪 {formulacion_key}")
                cell.font = formulacion_font
                cell.fill = formulacion_fill
                ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=7)
                row += 1
                
                # Items de la formulación
                for item in items:
                    cliente_display = f"{item['cliente_nombre']} ({item['cliente_nit']})"
                    
                    ws.cell(row=row, column=1, value=cliente_display)
                    ws.cell(row=row, column=2, value=item['categoria'] or '-')
                    ws.cell(row=row, column=3, value=item['formulacion'] or '-')
                    ws.cell(row=row, column=4, value=item['referencia'] or '-')
                    ws.cell(row=row, column=5, value=item['pedido_id'])
                    
                    # Cantidad y peso con formato numérico y alineación derecha
                    cantidad_cell = ws.cell(row=row, column=6, value=round(item['total_cantidad'], 2))
                    cantidad_cell.alignment = right_alignment
                    peso_cell = ws.cell(row=row, column=7, value=round(item['total_peso'], 2))
                    peso_cell.alignment = right_alignment
                    
                    row += 1
                
                # Subtotal de Formulación
                subtotal_cell = ws.cell(row=row, column=5, value=f"🧮 Subtotal {formulacion_key}:")
                subtotal_cell.font = subtotal_font
                subtotal_cell.fill = subtotal_fill
                subtotal_cell.alignment = right_alignment
                
                # Merge las primeras 5 columnas para el texto del subtotal
                ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=5)
                
                # Subtotal cantidad
                subtotal_cantidad_cell = ws.cell(row=row, column=6, value=round(subtotales_formulacion[formulacion_key]['cantidad'], 2))
                subtotal_cantidad_cell.font = subtotal_font
                subtotal_cantidad_cell.fill = subtotal_fill
                subtotal_cantidad_cell.alignment = right_alignment
                
                # Subtotal peso
                subtotal_peso_cell = ws.cell(row=row, column=7, value=round(subtotales_formulacion[formulacion_key]['peso'], 2))
                subtotal_peso_cell.font = subtotal_font
                subtotal_peso_cell.fill = subtotal_fill
                subtotal_peso_cell.alignment = right_alignment
                
                row += 1
                
                # Línea en blanco para separar formulaciones
                row += 1
        else:
            # No hay resultados
            no_results_cell = ws.cell(row=row, column=1, value="No se encontraron resultados con los filtros seleccionados")
            ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=7)
            no_results_cell.alignment = center_alignment
            row += 1

        # Total General
        total_cell = ws.cell(row=row, column=5, value="🔢 TOTALES GENERALES:")
        total_cell.font = total_font
        total_cell.fill = total_fill
        total_cell.alignment = right_alignment
        
        # Merge las primeras 5 columnas para el texto del total
        ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=5)
        
        # Total cantidad
        total_cantidad_cell = ws.cell(row=row, column=6, value=round(total_cantidad, 2))
        total_cantidad_cell.font = total_font
        total_cantidad_cell.fill = total_fill
        total_cantidad_cell.alignment = right_alignment
        
        # Total peso
        total_peso_cell = ws.cell(row=row, column=7, value=round(total_peso, 2))
        total_peso_cell.font = total_font
        total_peso_cell.fill = total_fill
        total_peso_cell.alignment = right_alignment

        # Ajustar ancho de columnas
        column_widths = [30, 15, 20, 25, 12, 12, 15]  # Anchos específicos para cada columna
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