from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from config.database import db_config
from models import Cliente
from utils.helpers import get_current_year, DEPARTAMENTOS_CIUDADES
import pandas as pd
from sqlalchemy.exc import IntegrityError

clientes_bp = Blueprint('clientes', __name__, url_prefix='/clientes')  # Restore the prefix

# Move API route outside of the blueprint to handle it separately
api_clientes_bp = Blueprint('api_clientes', __name__, url_prefix='/api/clientes')

@api_clientes_bp.route('/buscar', methods=['GET'])
def buscar_api():
    """API para buscar cliente por NIT"""
    nit = request.args.get('nit')
    if not nit:
        return jsonify({'existe': False, 'error': 'NIT no proporcionado'}), 400
        
    db = db_config.get_session()
    try:
        cliente = db.query(Cliente).filter(Cliente.numero_identificacion == nit).first()
        if cliente:
            return jsonify({
                'existe': True,
                'id': cliente.id,
                'nombre_comercial': cliente.nombre_comercial,
                'razon_social': cliente.razon_social,
                'tipo_identificacion': cliente.tipo_identificacion,
                'numero_identificacion': cliente.numero_identificacion,
                'email': cliente.email,
                'telefono': cliente.telefono,
                'direccion': cliente.direccion,
                'ciudad': cliente.ciudad,
                'departamento': cliente.departamento
            })
        else:
            return jsonify({'existe': False})
    finally:
        db.close()

# Ruta específica para manejar /clientes sin barra final (evita redirect 308)
@clientes_bp.route('', methods=['GET'], strict_slashes=False)
@clientes_bp.route('/')
def lista():
    """Lista de clientes"""
    db = db_config.get_session()
    try:
        clientes = db.query(Cliente).all()
        current_year = get_current_year()
        return render_template('clientes_list.html', clientes=clientes, current_year=current_year)
    finally:
        db.close()

@clientes_bp.route('/agregar', methods=['GET', 'POST'])
def agregar():
    """Agregar nuevo cliente"""
    db = db_config.get_session()
    try:
        current_year = get_current_year()
        
        # Obtener parámetros de la URL para GET o del formulario para POST
        if request.method == 'POST':
            redirect_to = request.form.get('redirect_to', '')
            nit = request.form.get('nit', '')
        else:
            redirect_to = request.args.get('redirect_to', '')
            nit = request.args.get('nit', '')

        if request.method == 'POST':
            nombre = request.form.get('nombre_comercial')
            razon = request.form.get('razon_social')
            tipo = request.form.get('tipo_identificacion')
            numero = request.form.get('numero_identificacion')
            email = request.form.get('email')
            telefono = request.form.get('telefono')
            direccion = request.form.get('direccion')
            ciudad = request.form.get('ciudad')
            departamento = request.form.get('departamento')

            # Validación básica
            if not all([nombre, razon, tipo, numero, email, telefono, direccion, ciudad, departamento]):
                flash('Todos los campos son requeridos.', 'danger')
                return render_template('cliente_form.html', 
                                    current_year=current_year, 
                                    modo='agregar',
                                    nit_default=nit, 
                                    redirect_to=redirect_to,
                                    departamentos_ciudades=DEPARTAMENTOS_CIUDADES)
            
            # Verificar si ya existe un cliente con este número de identificación
            cliente_existente = db.query(Cliente).filter(Cliente.numero_identificacion == numero).first()
            if cliente_existente:
                flash(f'Ya existe un cliente registrado con el número de identificación {numero}. Por favor verifique el número o busque el cliente existente.', 'warning')
                return render_template('cliente_form.html', 
                                    current_year=current_year, 
                                    modo='agregar',
                                    nit_default=nit, 
                                    redirect_to=redirect_to,
                                    departamentos_ciudades=DEPARTAMENTOS_CIUDADES)
            
            try:
                # Crear el nuevo cliente
                cli = Cliente(
                    nombre_comercial=nombre,
                    razon_social=razon,
                    tipo_identificacion=tipo,
                    numero_identificacion=numero,
                    email=email,
                    telefono=telefono,
                    direccion=direccion,
                    ciudad=ciudad,
                    departamento=departamento
                )
                db.add(cli)
                db.commit()
                
                flash('Cliente agregado correctamente.', 'success')
                
                # Redirigir según corresponda
                if redirect_to:
                    if redirect_to == 'pedidos':
                        return redirect(url_for('pedidos.form', cliente_id=cli.id, show_welcome='true'))
                    elif redirect_to == '/pedidos/form':
                        return redirect('/pedidos/form')
                return redirect(url_for('clientes.lista'))
                
            except IntegrityError as e:
                db.rollback()
                # Manejar específicamente el error de clave duplicada
                if 'numero_identificacion' in str(e) or 'UNIQUE constraint failed' in str(e):
                    flash(f'Ya existe un cliente con el número de identificación {numero}. Por favor verifique el número.', 'warning')
                else:
                    flash('Error al guardar el cliente. Por favor intente nuevamente.', 'danger')
            except Exception as e:
                db.rollback()
                flash('Ocurrió un error inesperado. Por favor intente nuevamente.', 'danger')
                
        # Renderizar el formulario (GET o si hay error en POST)
        return render_template('cliente_form.html', 
                             current_year=current_year, 
                             modo='agregar',
                             nit_default=nit, 
                             redirect_to=redirect_to,
                             departamentos_ciudades=DEPARTAMENTOS_CIUDADES)
    finally:
        db.close()

@clientes_bp.route('/editar/<int:cliente_id>', methods=['GET', 'POST'])
def editar(cliente_id):
    """Editar cliente existente"""
    db = db_config.get_session()
    try:
        cli = db.query(Cliente).get(cliente_id)
        current_year = get_current_year()
        
        if not cli:
            flash('Cliente no encontrado.', 'danger')
            return redirect(url_for('clientes.lista'))
        
        if request.method == 'POST':
            nuevo_numero = request.form.get('numero_identificacion')
            
            # Verificar si se está cambiando el número de identificación y si ya existe
            if nuevo_numero != cli.numero_identificacion:
                cliente_existente = db.query(Cliente).filter(
                    Cliente.numero_identificacion == nuevo_numero,
                    Cliente.id != cliente_id
                ).first()
                
                if cliente_existente:
                    flash(f'Ya existe otro cliente con el número de identificación {nuevo_numero}. Por favor use un número diferente.', 'warning')
                    return render_template('cliente_form.html', 
                                         cliente=cli, 
                                         current_year=current_year, 
                                         modo='editar',
                                         departamentos_ciudades=DEPARTAMENTOS_CIUDADES)
            
            try:
                cli.nombre_comercial = request.form.get('nombre_comercial')
                cli.razon_social = request.form.get('razon_social')
                cli.tipo_identificacion = request.form.get('tipo_identificacion')
                cli.numero_identificacion = nuevo_numero
                cli.email = request.form.get('email')
                cli.telefono = request.form.get('telefono')
                cli.direccion = request.form.get('direccion')
                cli.ciudad = request.form.get('ciudad')
                cli.departamento = request.form.get('departamento')
                db.commit()
                flash('Cliente actualizado correctamente.', 'success')
                return redirect(url_for('clientes.lista'))
            except IntegrityError as e:
                db.rollback()
                # Manejar específicamente el error de clave duplicada
                if 'numero_identificacion' in str(e) or 'UNIQUE constraint failed' in str(e):
                    flash(f'Ya existe un cliente con el número de identificación {nuevo_numero}. Por favor verifique el número.', 'warning')
                else:
                    flash('Error al actualizar el cliente. Por favor intente nuevamente.', 'danger')
            except Exception as e:
                db.rollback()
                flash('Ocurrió un error inesperado. Por favor intente nuevamente.', 'danger')
        
        return render_template('cliente_form.html', 
                             cliente=cli, 
                             current_year=current_year, 
                             modo='editar',
                             departamentos_ciudades=DEPARTAMENTOS_CIUDADES)
    finally:
        db.close()

@clientes_bp.route('/eliminar/<int:cliente_id>', methods=['POST'])
def eliminar(cliente_id):
    """Eliminar cliente"""
    db = db_config.get_session()
    try:
        cli = db.query(Cliente).get(cliente_id)
        if cli:
            db.delete(cli)
            db.commit()
            flash('Cliente eliminado.', 'success')
        else:
            flash('Cliente no encontrado.', 'danger')
        return redirect(url_for('clientes.lista'))
    finally:
        db.close()

@clientes_bp.route('/ver/<int:cliente_id>')
def ver(cliente_id):
    """Ver detalles de un cliente"""
    db = db_config.get_session()
    try:
        cliente = db.query(Cliente).get(cliente_id)
        if not cliente:
            flash('Cliente no encontrado', 'danger')
            return redirect(url_for('clientes.lista'))
        return render_template('ver_cliente.html', cliente=cliente, current_year=get_current_year())
    finally:
        db.close()

@clientes_bp.route('/importar', methods=['GET', 'POST'])
def importar():
    """Importar clientes desde Excel"""
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
                    columnas_requeridas = ['nombre_comercial', 'tipo_identificacion', 'numero_identificacion']
                    for col in columnas_requeridas:
                        if col not in df.columns:
                            raise ValueError(f'Falta la columna requerida: {col}')
                    
                    # Procesar cada fila
                    resultados = {'exito': True, 'mensaje': 'Clientes importados correctamente', 'errores': []}
                    for _, fila in df.iterrows():
                        try:
                            numero_identificacion = str(fila.get('numero_identificacion', ''))
                            
                            # Verificar si ya existe un cliente con este número de identificación
                            cliente_existente = db.query(Cliente).filter(Cliente.numero_identificacion == numero_identificacion).first()
                            if cliente_existente:
                                resultados['errores'].append(f'Fila {_ + 2}: Ya existe un cliente con el número de identificación {numero_identificacion}')
                                continue
                            
                            cliente = Cliente(
                                nombre_comercial=fila.get('nombre_comercial', ''),
                                razon_social=fila.get('razon_social', fila.get('nombre_comercial', '')),
                                tipo_identificacion=fila.get('tipo_identificacion', ''),
                                numero_identificacion=numero_identificacion,
                                digito_verificacion=str(fila.get('digito_verificacion', '')) if pd.notna(fila.get('digito_verificacion')) else None,
                                direccion=fila.get('direccion', ''),
                                direccion_ciudad=fila.get('ciudad', ''),
                                direccion_departamento=fila.get('departamento', ''),
                                direccion_pais=fila.get('pais', 'Colombia'),
                                telefono=str(fila.get('telefono', '')),
                                email=fila.get('email', ''),
                                responsable=fila.get('responsable', ''),
                                cargo=fila.get('cargo', ''),
                                actividad_economica=fila.get('actividad_economica', '')
                            )
                            db.add(cliente)
                            db.commit()
                        except IntegrityError as e:
                            db.rollback()
                            if 'numero_identificacion' in str(e) or 'UNIQUE constraint failed' in str(e):
                                resultados['errores'].append(f'Fila {_ + 2}: El número de identificación {numero_identificacion} ya está registrado')
                            else:
                                resultados['errores'].append(f'Fila {_ + 2}: Error de base de datos - {str(e)}')
                        except Exception as e:
                            db.rollback()
                            resultados['errores'].append(f'Fila {_ + 2}: {str(e)}')
                    
                    if resultados['errores']:
                        resultados['exito'] = False
                        resultados['mensaje'] = 'Se produjeron algunos errores durante la importación'
                    
                    return render_template('importar_clientes.html', 
                                         resultados=resultados,
                                         current_year=current_year)
                    
                except Exception as e:
                    error_msg = f'Error al procesar el archivo: {str(e)}'
                    return render_template('importar_clientes.html', 
                                         resultados={'exito': False, 'mensaje': error_msg, 'errores': [error_msg]},
                                         current_year=current_year)
        
        return render_template('importar_clientes.html', current_year=current_year)
    finally:
        db.close()

@clientes_bp.route('/importar-clientes')
def redirect_importar():
    """Redirige a la página de importación de clientes"""
    return redirect(url_for('clientes.importar'))