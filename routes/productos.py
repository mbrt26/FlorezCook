from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from config.database import db_config
from models import Producto
from utils.helpers import get_current_year
import pandas as pd
from sqlalchemy import or_, and_
import logging

# Configurar logger
logger = logging.getLogger(__name__)

productos_bp = Blueprint('productos', __name__, url_prefix='/productos')

# Ruta específica para manejar /productos sin barra final (evita redirect 308)
@productos_bp.route('', methods=['GET'], strict_slashes=False)
@productos_bp.route('/')
def lista():
    """Lista de productos"""
    db = db_config.get_session()
    try:
        productos = db.query(Producto).all()
        
        # Obtener valores únicos para los filtros
        grupos = db.query(Producto.formulacion_grupo).distinct().filter(Producto.formulacion_grupo.isnot(None)).all()
        lineas = db.query(Producto.categoria_linea).distinct().filter(Producto.categoria_linea.isnot(None)).all()
        
        grupos = [g[0] for g in grupos if g[0]]
        lineas = [l[0] for l in lineas if l[0]]
        
        current_year = get_current_year()
        return render_template('productos_list.html', 
                             productos=productos, 
                             grupos=grupos,
                             lineas=lineas,
                             current_year=current_year)
    finally:
        db.close()

@productos_bp.route('/api/buscar')
def api_buscar():
    """API para búsqueda de productos con autocompletado para pedidos"""
    db = db_config.get_session()
    try:
        # Obtener término de búsqueda
        termino = request.args.get('q', '').strip()
        limite = int(request.args.get('limit', 10))  # Limitar resultados para rendimiento
        
        if len(termino) < 1:  # Mínimo 1 carácter para iniciar búsqueda
            return jsonify([])
        
        # Buscar productos por código, referencia o línea
        query = db.query(Producto).filter(
            or_(
                Producto.codigo.ilike(f'%{termino}%'),
                Producto.referencia_de_producto.ilike(f'%{termino}%'),
                Producto.categoria_linea.ilike(f'%{termino}%')
            )
        ).limit(limite)
        
        productos = query.all()
        
        # Formatear resultados para autocompletado
        resultados = []
        for p in productos:
            resultados.append({
                'id': p.id,
                'codigo': p.codigo,
                'referencia': p.referencia_de_producto,
                'display': f"{p.codigo} - {p.referencia_de_producto} - {p.categoria_linea or 'Sin línea'}",
                'gramaje_g': p.gramaje_g,
                'formulacion_grupo': p.formulacion_grupo or '',
                'categoria_linea': p.categoria_linea or '',
                'presentacion1': p.presentacion1 or '',
                'presentacion2': p.presentacion2 or ''
            })
        
        return jsonify(resultados)
        
    except Exception as e:
        return jsonify([]), 500
    finally:
        db.close()

@productos_bp.route('/api/filtrar')
def api_filtrar():
    """API para filtrar productos en tiempo real"""
    db = db_config.get_session()
    try:
        # Obtener parámetros de filtrado
        busqueda = request.args.get('busqueda', '').strip()
        grupo = request.args.get('grupo', '').strip()
        linea = request.args.get('linea', '').strip()
        
        # Construir query base
        query = db.query(Producto)
        
        # Aplicar filtros
        if busqueda:
            query = query.filter(
                or_(
                    Producto.codigo.ilike(f'%{busqueda}%'),
                    Producto.referencia_de_producto.ilike(f'%{busqueda}%')
                )
            )
        
        if grupo:
            query = query.filter(Producto.formulacion_grupo == grupo)
            
        if linea:
            query = query.filter(Producto.categoria_linea == linea)
        
        productos = query.all()
        
        # Convertir a JSON
        productos_data = []
        for p in productos:
            productos_data.append({
                'id': p.id,
                'codigo': p.codigo,
                'referencia_de_producto': p.referencia_de_producto,
                'gramaje_g': p.gramaje_g,
                'formulacion_grupo': p.formulacion_grupo or '',
                'categoria_linea': p.categoria_linea or '',
                'presentacion1': p.presentacion1 or '',
                'presentacion2': p.presentacion2 or ''
            })
        
        return jsonify({
            'success': True,
            'productos': productos_data,
            'total': len(productos_data)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        db.close()

@productos_bp.route('/agregar', methods=['GET', 'POST'])
def agregar():
    """Agregar nuevo producto"""
    db = db_config.get_session()
    try:
        current_year = get_current_year()
        if request.method == 'POST':
            codigo = request.form.get('codigo')
            referencia = request.form.get('referencia_de_producto')
            gramaje = request.form.get('gramaje_g')
            grupo = request.form.get('formulacion_grupo')
            linea = request.form.get('categoria_linea')
            presentacion1 = request.form.get('presentacion1')
            presentacion2 = request.form.get('presentacion2')
            
            if not codigo or not referencia or not gramaje:
                flash('Todos los campos obligatorios deben ser completados.', 'danger')
                return render_template('producto_form.html', current_year=current_year, modo='agregar')
            
            prod = Producto(
                codigo=codigo, 
                referencia_de_producto=referencia, 
                gramaje_g=gramaje, 
                formulacion_grupo=grupo, 
                categoria_linea=linea,
                presentacion1=presentacion1,
                presentacion2=presentacion2
            )
            db.add(prod)
            db.commit()
            flash('Producto agregado correctamente.', 'success')
            return redirect(url_for('productos.lista'))
        
        return render_template('producto_form.html', current_year=current_year, modo='agregar')
    finally:
        db.close()

@productos_bp.route('/editar/<int:producto_id>', methods=['GET', 'POST'])
def editar(producto_id):
    """Editar producto existente"""
    db = db_config.get_session()
    try:
        prod = db.query(Producto).get(producto_id)
        current_year = get_current_year()
        
        if not prod:
            flash('Producto no encontrado.', 'danger')
            return redirect(url_for('productos.lista'))
        
        if request.method == 'POST':
            prod.codigo = request.form.get('codigo')
            prod.referencia_de_producto = request.form.get('referencia_de_producto')
            prod.gramaje_g = request.form.get('gramaje_g')
            prod.formulacion_grupo = request.form.get('formulacion_grupo')
            prod.categoria_linea = request.form.get('categoria_linea')
            prod.presentacion1 = request.form.get('presentacion1')
            prod.presentacion2 = request.form.get('presentacion2')
            db.commit()
            flash('Producto actualizado correctamente.', 'success')
            return redirect(url_for('productos.lista'))
        
        return render_template('producto_form.html', producto=prod, current_year=current_year, modo='editar')
    finally:
        db.close()

@productos_bp.route('/eliminar/<int:producto_id>', methods=['POST'])
def eliminar(producto_id):
    """Eliminar producto"""
    db = db_config.get_session()
    try:
        prod = db.query(Producto).get(producto_id)
        if prod:
            db.delete(prod)
            db.commit()
            flash('Producto eliminado.', 'success')
        else:
            flash('Producto no encontrado.', 'danger')
        return redirect(url_for('productos.lista'))
    finally:
        db.close()

@productos_bp.route('/eliminar-multiple', methods=['POST'])
def eliminar_multiple():
    """Eliminar múltiples productos"""
    db = db_config.get_session()
    try:
        # Obtener los IDs de productos a eliminar desde el JSON
        data = request.get_json()
        if not data or 'ids' not in data:
            return jsonify({'success': False, 'error': 'No se proporcionaron IDs de productos'})
        
        ids = data['ids']
        if not isinstance(ids, list) or len(ids) == 0:
            return jsonify({'success': False, 'error': 'Lista de IDs inválida'})
        
        # Validar que todos los IDs sean enteros
        try:
            ids = [int(id_str) for id_str in ids]
        except (ValueError, TypeError):
            return jsonify({'success': False, 'error': 'IDs de productos inválidos'})
        
        # Buscar productos existentes
        productos = db.query(Producto).filter(Producto.id.in_(ids)).all()
        productos_encontrados = len(productos)
        
        if productos_encontrados == 0:
            return jsonify({'success': False, 'error': 'No se encontraron productos para eliminar'})
        
        # Obtener códigos de productos para el log
        codigos_eliminados = [p.codigo for p in productos]
        
        # Eliminar productos
        for producto in productos:
            db.delete(producto)
        
        db.commit()
        
        # Mensaje de éxito
        if productos_encontrados == len(ids):
            mensaje = f'Se eliminaron {productos_encontrados} productos correctamente'
        else:
            mensaje = f'Se eliminaron {productos_encontrados} de {len(ids)} productos (algunos no se encontraron)'
        
        # Log de la acción (opcional)
        logger.info(f"Eliminación múltiple de productos por usuario. IDs eliminados: {ids}, Códigos: {codigos_eliminados}")
        
        return jsonify({
            'success': True, 
            'message': mensaje,
            'eliminados': productos_encontrados,
            'codigos': codigos_eliminados
        })
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error en eliminación múltiple de productos: {str(e)}")
        return jsonify({'success': False, 'error': f'Error al eliminar productos: {str(e)}'})
    finally:
        db.close()

@productos_bp.route('/ver/<int:producto_id>')
def ver(producto_id):
    """Ver detalles de un producto"""
    db = db_config.get_session()
    try:
        producto = db.query(Producto).get(producto_id)
        if not producto:
            flash('Producto no encontrado', 'danger')
            return redirect(url_for('productos.lista'))
        return render_template('ver_producto.html', producto=producto)
    finally:
        db.close()

@productos_bp.route('/importar', methods=['GET', 'POST'])
def importar():
    """Importar productos desde Excel"""
    db = db_config.get_session()
    try:
        current_year = get_current_year()
        
        if request.method == 'POST':
            if 'archivo' not in request.files:
                return redirect(request.url)
            
            archivo = request.files['archivo']
            if archivo.filename == '':
                return redirect(request.url)
                
            if archivo:
                try:
                    # Leer el archivo Excel
                    df = pd.read_excel(archivo)
                    
                    # Validar columnas requeridas
                    columnas_requeridas = ['codigo', 'referencia_de_producto', 'gramaje_g', 'formulacion_grupo', 'categoria_linea']
                    for col in columnas_requeridas:
                        if col not in df.columns:
                            raise ValueError(f'Falta la columna requerida: {col}')
                    
                    # Procesar cada fila
                    resultados = {'exito': True, 'mensaje': 'Productos importados correctamente', 'errores': []}
                    for _, fila in df.iterrows():
                        try:
                            # Función para manejar valores NaN
                            def safe_get(key, default=''):
                                val = fila.get(key, default)
                                return default if pd.isna(val) else val
                            
                            def safe_get_float(key, default=0.0):
                                val = fila.get(key, default)
                                if pd.isna(val):
                                    return default
                                try:
                                    return float(val)
                                except (ValueError, TypeError):
                                    return default
                            
                            producto = Producto(
                                codigo=safe_get('codigo'),
                                referencia_de_producto=safe_get('referencia_de_producto'),
                                gramaje_g=safe_get_float('gramaje_g', 0.0),
                                formulacion_grupo=safe_get('formulacion_grupo'),
                                categoria_linea=safe_get('categoria_linea'),
                                descripcion=safe_get('descripcion'),
                                presentacion1=safe_get('presentacion1'),
                                presentacion2=safe_get('presentacion2'),
                                precio_unitario=safe_get_float('precio_unitario', 0.0),
                                unidad_medida=safe_get('unidad_medida', 'unidad'),
                                estado='Activo' if str(safe_get('estado', '')).lower() in ['activo', '1', 'sí', 'si', 'true'] else 'Inactivo'
                            )
                            db.add(producto)
                            db.commit()
                        except Exception as e:
                            db.rollback()
                            resultados['errores'].append(f'Error en fila {_ + 2}: {str(e)}')
                    
                    if resultados['errores']:
                        resultados['exito'] = False
                        resultados['mensaje'] = 'Se produjeron algunos errores durante la importación'
                    
                    return render_template('importar_productos.html', 
                                         resultados=resultados,
                                         current_year=current_year)
                    
                except Exception as e:
                    error_msg = f'Error al procesar el archivo: {str(e)}'
                    return render_template('importar_productos.html', 
                                         resultados={'exito': False, 'mensaje': error_msg, 'errores': [error_msg]},
                                         current_year=current_year)
        
        return render_template('importar_productos.html', current_year=current_year)
    finally:
        db.close()

@productos_bp.route('/importar-productos')
def redirect_importar():
    """Redirige a la página de importación de productos"""
    return redirect(url_for('productos.importar'))