from flask import Blueprint, render_template, request, redirect, url_for, flash
from config.database import db_config
from models import Producto, Cliente, Pedido, PedidoProducto
import business_logic
from utils.helpers import get_current_year
from sqlalchemy import func
import logging

# Configurar logging para esta ruta
logger = logging.getLogger(__name__)

pedidos_bp = Blueprint('pedidos', __name__, url_prefix='/pedidos')

# Ruta específica para manejar /pedidos sin barra final (evita redirect 308)
@pedidos_bp.route('', methods=['GET', 'POST'], strict_slashes=False)
@pedidos_bp.route('/', methods=['GET', 'POST'])
@pedidos_bp.route('/form', methods=['GET', 'POST'])
def form():
    """Formulario para crear nuevos pedidos - OPTIMIZADO SIN REDIRECCIÓN"""
    db = None
    try:
        db = db_config.get_session()
        
        # OPTIMIZACIÓN: Usar caché de productos en lugar de consulta directa
        productos_dict = business_logic.get_productos_cached(db)
        
        current_year = get_current_year()

        # Get client ID and show_welcome flag from query params
        cliente_id = request.args.get('cliente_id')
        show_welcome = request.args.get('show_welcome', '').lower() == 'true'
        cliente_data = {}
        if cliente_id:
            cliente = db.query(Cliente).get(cliente_id)
            if cliente:
                cliente_data = {
                    'direccion_entrega': cliente.direccion,
                    'ciudad_entrega': cliente.ciudad,
                    'departamento_entrega': cliente.departamento,
                    'show_welcome_message': show_welcome
                }

        if request.method == 'POST':
            form_data = dict(request.form)
            pedido_items = []
            idx = 0
            while True:
                key = f'producto_id_{idx}'
                if key not in form_data:
                    break
                if form_data.get(key):
                    pedido_items.append({
                        'producto_id': int(form_data.get(f'producto_id_{idx}', 0)),
                        'cantidad': form_data.get(f'cantidad_{idx}', ''),
                        'gramaje_g_item': form_data.get(f'gramaje_g_item_{idx}', ''),
                        'peso_total_g_item': form_data.get(f'peso_total_g_item_{idx}', ''),
                        'grupo_item': form_data.get(f'grupo_item_{idx}', ''),
                        'linea_item': form_data.get(f'linea_item_{idx}', ''),
                        'fecha_de_entrega_item': form_data.get(f'fecha_de_entrega_item_{idx}', ''),
                        'observaciones_item': form_data.get(f'observaciones_item_{idx}', ''),
                        'estado_del_pedido_item': form_data.get(f'estado_del_pedido_item_{idx}', 'Pendiente'),
                    })
                idx += 1

            form_data['pedido_items'] = pedido_items
            success, result = business_logic.guardar_pedido_completo(db, form_data)

            if success:
                flash('Pedido guardado correctamente.', 'success')
                return redirect(url_for('pedidos.form'))
            else:
                for error in result:
                    flash(error, 'danger')
                form_state = business_logic.inicializar_estado_nuevo_pedido()
                form_state.update(form_data)
                form_state['show_seccion_registro'] = bool(form_data.get('show_seccion_registro'))
                form_state['show_seccion_despacho'] = True
                form_state['show_subform_pedido'] = True
                return render_template('pedido_form.html', 
                                     form_data=form_state, 
                                     productos=productos_dict, 
                                     current_year=current_year)
        else:
            form_state = business_logic.inicializar_estado_nuevo_pedido()
            form_state.update(cliente_data)  # Prefill with client data
            show_welcome_message = request.args.get('show_welcome', '').lower() == 'true'
            
            return render_template('pedido_form.html', 
                                form_data=form_state, 
                                productos=productos_dict, 
                                current_year=current_year,
                                show_welcome_message=show_welcome_message)
    except Exception as e:
        logger.error(f"Error interno del servidor en pedidos.form: {str(e)}", exc_info=True)
        return f"Error interno del servidor: {str(e)}", 500
    finally:
        if db:
            db.close()

@pedidos_bp.route('/lista')
def lista():
    """Lista de pedidos - OPTIMIZADA"""
    db = db_config.get_session()
    try:
        # OPTIMIZACIÓN: Usar eager loading para evitar consultas N+1
        from sqlalchemy.orm import joinedload
        
        pedidos = db.query(Pedido).options(
            joinedload(Pedido.cliente_asociado),
            joinedload(Pedido.items).joinedload(PedidoProducto.producto_asociado)
        ).order_by(Pedido.fecha_creacion.desc()).limit(50).all()  # Limitar a 50 para mejor rendimiento
        
        current_year = get_current_year()
        return render_template('pedidos_lista.html', pedidos=pedidos, current_year=current_year)
    finally:
        db.close()

@pedidos_bp.route('/ver/<int:pedido_id>')
def ver(pedido_id):
    """Ver detalles de un pedido específico"""
    db = db_config.get_session()
    try:
        from sqlalchemy.orm import joinedload
        
        pedido = db.query(Pedido).options(
            joinedload(Pedido.cliente_asociado),
            joinedload(Pedido.items).joinedload(PedidoProducto.producto_asociado)
        ).filter(Pedido.id == pedido_id).first()
        
        if not pedido:
            flash('Pedido no encontrado', 'danger')
            return redirect(url_for('pedidos.lista'))
        
        # Calculate total weight and value
        total_peso = sum(item.peso_total_g_item or 0 for item in pedido.items)
        total_valor = sum((item.cantidad or 0) * (item.producto_asociado.gramaje_g or 0) for item in pedido.items)
        
        current_year = get_current_year()
        return render_template('ver_pedido.html', 
                             pedido=pedido, 
                             total_peso=total_peso,
                             total_valor=total_valor,
                             current_year=current_year)
    finally:
        db.close()

@pedidos_bp.route('/eliminar/<int:pedido_id>', methods=['POST'])
def eliminar(pedido_id):
    """Eliminar un pedido específico"""
    db = db_config.get_session()
    try:
        pedido = db.query(Pedido).get(pedido_id)
        if not pedido:
            flash('Pedido no encontrado', 'danger')
            return redirect(url_for('pedidos.lista'))
            
        db.delete(pedido)
        db.commit()
        flash('Pedido eliminado correctamente', 'success')
        return redirect(url_for('pedidos.lista'))
    except Exception as e:
        db.rollback()
        flash(f'Error al eliminar el pedido: {str(e)}', 'danger')
        return redirect(url_for('pedidos.lista'))
    finally:
        db.close()

@pedidos_bp.route('/consolidado')
def consolidado():
    """Mostrar vista consolidada de productos pedidos"""
    db = db_config.get_session()
    try:
        # Consulta para obtener productos consolidados con su cantidad total
        productos_consolidados = db.query(
            Producto.referencia_de_producto,
            Producto.codigo,
            Producto.formulacion_grupo,
            Producto.categoria_linea,
            func.sum(PedidoProducto.cantidad).label('total_cantidad')
        ).join(
            PedidoProducto, Producto.id == PedidoProducto.producto_id
        ).group_by(
            Producto.referencia_de_producto,
            Producto.codigo,
            Producto.formulacion_grupo,
            Producto.categoria_linea
        ).all()
        
        current_year = get_current_year()
        return render_template('pedidos_consolidado.html', 
                             productos=productos_consolidados,
                             current_year=current_year)
    finally:
        db.close()

@pedidos_bp.route('/editar/<int:pedido_id>', methods=['GET', 'POST'])
def editar(pedido_id):
    """Editar un pedido existente"""
    db = db_config.get_session()
    try:
        from sqlalchemy.orm import joinedload
        import datetime
        
        pedido = db.query(Pedido).options(
            joinedload(Pedido.cliente_asociado),
            joinedload(Pedido.items).joinedload(PedidoProducto.producto_asociado)
        ).filter(Pedido.id == pedido_id).first()
        
        if not pedido:
            flash('Pedido no encontrado', 'danger')
            return redirect(url_for('pedidos.lista'))

        productos = db.query(Producto).all()
        estados = ['Pendiente', 'En Proceso', 'Completado', 'Cancelado', 'Entregado']
        
        if request.method == 'POST':
            try:
                logger.info(f"Actualizando pedido con ID: {pedido_id}")
                # Update pedido general info
                pedido.estado_pedido_general = request.form.get('estado')
                pedido.alerta = request.form.get('alerta')
                pedido.despacho_tipo = request.form.get('despacho_tipo')
                pedido.direccion_entrega = request.form.get('direccion_entrega')
                pedido.ciudad_entrega = request.form.get('ciudad_entrega')
                pedido.departamento_entrega = request.form.get('departamento_entrega')
                pedido.despacho_horario_atencion = request.form.get('despacho_horario_atencion')
                pedido.observaciones_despacho = request.form.get('observaciones_despacho')

                # Delete existing items
                logger.info(f"Eliminando {len(pedido.items)} items existentes del pedido")
                for item in pedido.items:
                    db.delete(item)
                
                # Add new items
                logger.info("Agregando nuevos items al pedido")
                idx = 0
                while True:
                    producto_id_key = f'producto_id_{idx}'
                    if producto_id_key not in request.form:
                        break
                        
                    if request.form.get(producto_id_key):
                        # Convert fecha_de_entrega_item string to Python date object
                        fecha_entrega_str = request.form.get(f'fecha_de_entrega_item_{idx}')
                        fecha_entrega = datetime.date.fromisoformat(fecha_entrega_str) if fecha_entrega_str else None
                        
                        # AGREGADO: Usar fecha actual para fecha_pedido_item
                        fecha_pedido_item = datetime.date.today()
                        
                        item = PedidoProducto(
                            pedido_id=pedido.id,
                            producto_id=int(request.form.get(producto_id_key)),
                            fecha_pedido_item=fecha_pedido_item,  # AGREGADO: Columna faltante
                            cantidad=float(request.form.get(f'cantidad_{idx}')),
                            gramaje_g_item=float(request.form.get(f'gramaje_g_item_{idx}', 0)),
                            peso_total_g_item=float(request.form.get(f'peso_total_g_item_{idx}', 0)),
                            grupo_item=request.form.get(f'grupo_item_{idx}', ''),
                            linea_item=request.form.get(f'linea_item_{idx}', ''),
                            fecha_de_entrega_item=fecha_entrega,
                            estado_del_pedido_item=request.form.get(f'estado_del_pedido_item_{idx}', 'Pendiente'),
                            observaciones_item=request.form.get(f'observaciones_item_{idx}', '')
                        )
                        db.add(item)
                    idx += 1

                db.commit()
                flash('Pedido actualizado correctamente', 'success')
                return redirect(url_for('pedidos.ver', pedido_id=pedido_id))
            except Exception as e:
                db.rollback()
                logger.error(f'Error al actualizar el pedido: {str(e)}', exc_info=True)
                flash(f'Error al actualizar el pedido: {str(e)}', 'danger')

        return render_template('editar_pedido.html', 
                             pedido=pedido,
                             productos=productos,
                             estados=estados)
    except Exception as e:
        logger.error(f'Error al cargar el pedido: {str(e)}', exc_info=True)
        flash(f'Error al cargar el pedido: {str(e)}', 'danger')
        return redirect(url_for('pedidos.lista'))
    finally:
        db.close()