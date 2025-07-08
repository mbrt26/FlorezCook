import os
import logging
from sqlalchemy.orm import Session
# Corregir el import de models para que funcione en App Engine Standard
from models import Cliente, Producto, Pedido, PedidoProducto
import datetime
from datetime import date, timedelta

# Configurar logger para el módulo
logger = logging.getLogger(__name__)

def inicializar_estado_nuevo_pedido():
    """
    Prepara el estado inicial para un nuevo formulario de Pedido.
    Esto corresponde a la lógica de 'Paso 1. Configuración Inicial' en Deluge.
    Define qué secciones/campos están inicialmente visibles y sus valores por defecto.
    
    Retorna:
        dict: Un diccionario con el estado inicial del formulario.
              Las claves 'show_*' indican visibilidad, y otras claves los valores de los campos.
    """
    initial_state = {
        # Campos del formulario Pedidos y su estado inicial según "Paso 1"
        'numero_identificacion_cliente_ingresado': '', # Campo para ingresar la identificación
        
        'nombre_cliente_ingresado': '', # Limpiado por "Paso 1", aunque el form lo defina con "Su Empresa"
                                     # El valor original "Su Empresa" se maneja en "Paso 2" si no hay cliente.
        
        'alerta_value': '', # Para el campo Alerta

        # Indicadores de visibilidad para la UI (plantilla HTML/JavaScript)
        'show_nombre_cliente_ingresado': False, # Corresponde a 'hide Nombre_Cliente'
        'show_clientes_inactivo': False,    # Corresponde a 'hide Clientes_Inactivo' (campo de búsqueda/selección)
        'show_alerta': False,               # Corresponde a 'hide Alerta'
        
        # Campos de la sección de Registro (inicialmente ocultos y vacíos)
        'nombre_comercial_r': '',
        'razon_social_r': '',
        'tipo_identificacion_r': None, # O el valor por defecto de un picklist si aplica
        'numero_identificacion_r': '',
        'email_r': '',
        'telefono_r': '',
        'direccion_r_linea1': '',
        'direccion_r_linea2': '',
        'direccion_r_ciudad': '',
        'direccion_r_departamento': '',
        'direccion_r_codigo_postal': '',
        'direccion_r_pais': '', # Podría tener un default como 'Colombia'

        # Campos de la sección de Despacho (inicialmente ocultos y vacíos)
        'despacho_tipo': None, # O el valor por defecto de un picklist
        'despacho_sede': '',
        'despacho_direccion_linea1': '',
        'despacho_direccion_linea2': '',
        'despacho_direccion_ciudad': '',
        'despacho_direccion_departamento': '',
        'despacho_direccion_codigo_postal': '',
        'despacho_direccion_pais': '', # Podría tener un default
        'despacho_horario_atencion': '',
        'despacho_observaciones': '',
        'estado_pedido_general': 'En Proceso', # Valor inicial del picklist en Zoho

        # Para el subformulario de Pedido (items del pedido), inicialmente una lista vacía
        'pedido_items': [] 
    }
    return initial_state

def manejar_input_identificacion_cliente(db: Session, numero_identificacion_ingresado: str, current_form_state: dict) -> dict:
    """
    Maneja la lógica cuando el usuario ingresa un Número de Identificación en el formulario de Pedidos.
    Corresponde a 'Paso 2. Lógica Principal' de Deluge.

    Args:
        db: Sesión de SQLAlchemy para interactuar con la base de datos.
        numero_identificacion_ingresado: El número de identificación que el usuario ingresó.
        current_form_state: El estado actual del formulario (diccionario).

    Returns:
        dict: El nuevo estado del formulario después de aplicar la lógica.
    """
    new_state = current_form_state.copy()

    if not numero_identificacion_ingresado:
        # Si el campo NIT está vacío, ocultar todo de nuevo (resetear)
        new_state['show_nombre_cliente_ingresado'] = False
        new_state['nombre_cliente_ingresado'] = '' # Limpiar el nombre del cliente
        new_state['show_seccion_registro'] = False
        new_state['show_seccion_despacho'] = False
        new_state['show_subform_pedido'] = False
        new_state['alerta_value'] = '' # Limpiar cualquier alerta
        # Limpiar campos de registro (opcional, pero buena práctica como en Deluge)
        new_state['nombre_comercial_r'] = ''
        new_state['razon_social_r'] = ''
        new_state['tipo_identificacion_r'] = None
        new_state['numero_identificacion_r'] = ''
        new_state['email_r'] = ''
        new_state['telefono_r'] = ''
        new_state['direccion_r_linea1'] = ''
        # ... (limpiar otros campos de dirección si es necesario)
        return new_state

    # Buscar el cliente en la base de datos
    cliente_existente = db.query(Cliente).filter(Cliente.numero_identificacion == numero_identificacion_ingresado).first()

    if cliente_existente:
        # --- Cliente ENCONTRADO ---
        new_state['show_seccion_registro'] = False
        # Limpiar campos de registro por si acaso el usuario cambió de opinión
        new_state['nombre_comercial_r'] = ''
        new_state['razon_social_r'] = ''
        new_state['tipo_identificacion_r'] = None
        new_state['numero_identificacion_r'] = ''
        new_state['email_r'] = ''
        new_state['telefono_r'] = ''
        new_state['direccion_r_linea1'] = '' 
        # ... (limpiar otros campos de dirección de registro)

        new_state['nombre_cliente_ingresado'] = cliente_existente.nombre_comercial # Asumiendo que Nombre_Cliente es nombre_comercial
        new_state['show_nombre_cliente_ingresado'] = True
        
        new_state['show_seccion_despacho'] = True
        new_state['show_subform_pedido'] = True
        new_state['alerta_value'] = '' # Limpiar alerta

        # Nota: La lógica de Zoho "hide Pedido.Linea; hide Pedido.Peso_Total_g; ..."
        # se refiere a columnas dentro del subformulario. En una aplicación web,
        # esto se manejaría típicamente en la plantilla que renderiza el subformulario
        # o mediante JavaScript en el frontend, posiblemente influenciado por otro estado
        # o lógica como 'InfoProductos'.

    else:
        # --- Cliente NO ENCONTRADO ---
        new_state['alerta_value'] = "Por favor registrarse como cliente"
        new_state['show_nombre_cliente_ingresado'] = False
        new_state['nombre_cliente_ingresado'] = '' # Mantener limpio o según la lógica de "Su Empresa"
        
        new_state['show_seccion_registro'] = True
        # Poblar el No. Identificación en la sección de registro con el valor ya ingresado
        new_state['numero_identificacion_r'] = numero_identificacion_ingresado
        # El Nombre_Cliente en el formulario Pedidos de Zoho tiene un valor inicial de "Su Empresa".
        # Si no se encuentra el cliente, el campo Nombre_Cliente se oculta.
        # Si se muestra la sección de registro, el usuario ingresará los datos allí.
        # El campo Nombre_Comercial_R de la sección de registro se usará para el nuevo cliente.

        new_state['show_seccion_despacho'] = True
        new_state['show_subform_pedido'] = True
        
        # Nota: Similar al caso de cliente encontrado, el ocultamiento de columnas específicas
        # del subformulario (Pedido.Grupo, Pedido.Linea, etc.) es más una tarea del frontend.

    return new_state

def actualizar_info_producto_en_pedido(db: Session, producto_id_seleccionado: int, cantidad: int, item_index: int, current_pedido_items: list) -> list:
    """
    Actualiza la información de un ítem específico en la lista de productos de un pedido,
    basado en el producto seleccionado y la cantidad. Replica la lógica de 'InfoProductos'.

    Args:
        db: Sesión de SQLAlchemy.
        producto_id_seleccionado: ID del producto que el usuario seleccionó para este ítem.
        cantidad: La cantidad ingresada para este ítem (ahora es entero).
        item_index: El índice del ítem en la lista current_pedido_items que se va a actualizar.
        current_pedido_items: La lista actual de diccionarios, donde cada diccionario representa un ítem del pedido.

    Returns:
        list: La lista actualizada de ítems del pedido.
    """
    updated_items = [item.copy() for item in current_pedido_items] # Trabajar con una copia

    if item_index < 0 or item_index >= len(updated_items):
        # Manejar índice inválido, aunque esto debería ser prevenido por la UI
        # Podríamos lanzar un error o simplemente retornar los items sin cambios
        print(f"Error: Índice de ítem ({item_index}) fuera de rango.")
        return updated_items

    item_a_actualizar = updated_items[item_index]

    if producto_id_seleccionado is not None:
        producto_info = db.query(Producto).filter(Producto.id == producto_id_seleccionado).first()

        if producto_info:
            item_a_actualizar['producto_id'] = producto_info.id
            item_a_actualizar['gramaje_g_item'] = producto_info.gramaje_g
            item_a_actualizar['linea_item'] = producto_info.categoria_linea
            item_a_actualizar['grupo_item'] = producto_info.formulacion_grupo
            
            # Calcular el peso total basado en la cantidad (entero) y el gramaje del producto
            if cantidad is not None and producto_info.gramaje_g is not None:
                item_a_actualizar['peso_total_g_item'] = cantidad * producto_info.gramaje_g
            else:
                item_a_actualizar['peso_total_g_item'] = 0.0
            
            # Establecer Fecha de Entrega por defecto (Hoy + 2 días)
            fecha_entrega_dt = datetime.date.today() + datetime.timedelta(days=2)
            item_a_actualizar['fecha_de_entrega_item'] = fecha_entrega_dt.isoformat() # Guardar como string YYYY-MM-DD
            
            # Opcional: Actualizar campos de display si los tienes en tu estructura de item_a_actualizar
            item_a_actualizar['producto_codigo_display'] = producto_info.codigo
            item_a_actualizar['producto_referencia_display'] = producto_info.referencia_de_producto

        else:
            # Producto no encontrado, limpiar campos relacionados (similar a deseleccionar)
            item_a_actualizar['producto_id'] = None
            item_a_actualizar['gramaje_g_item'] = None
            item_a_actualizar['linea_item'] = ''
            item_a_actualizar['grupo_item'] = ''
            item_a_actualizar['peso_total_g_item'] = None
            item_a_actualizar['fecha_de_entrega_item'] = None
            item_a_actualizar['producto_codigo_display'] = ''
            item_a_actualizar['producto_referencia_display'] = ''
    else:
        # Si producto_id_seleccionado es None (ej. se deselecciona el producto)
        item_a_actualizar['producto_id'] = None
        item_a_actualizar['gramaje_g_item'] = None
        item_a_actualizar['linea_item'] = ''
        item_a_actualizar['grupo_item'] = ''
        item_a_actualizar['peso_total_g_item'] = None
        item_a_actualizar['fecha_de_entrega_item'] = None
        item_a_actualizar['producto_codigo_display'] = ''
        item_a_actualizar['producto_referencia_display'] = ''

    return updated_items

def validar_datos_pedido(form_data: dict) -> list:
    """
    Valida los datos del formulario de pedido antes de guardarlo.
    Corresponde a 'Paso 4. Validacion_de_info' de Deluge.

    Args:
        form_data: Un diccionario que contiene todos los datos del formulario de pedido,
                   incluyendo el estado de visibilidad de las secciones y los items del pedido.

    Returns:
        list: Una lista de mensajes de error. Vacía si no hay errores.
    """
    errors = []

    # Validar información del cliente
    if not form_data.get('numero_identificacion_cliente_ingresado'):
        errors.append("El Número de Identificación del cliente es obligatorio.")
    
    # Si no hay un cliente_id, verificar que se proporcione un nombre de cliente
    if not form_data.get('cliente_id') and not form_data.get('nombre_cliente_ingresado'):
        errors.append("El nombre del cliente es obligatorio.")

    # Validaciones si es un cliente nuevo (sección de registro visible y utilizada)
    if form_data.get('show_seccion_registro'):
        if not form_data.get('nombre_comercial_r'):
            errors.append("Nombre Comercial es obligatorio para nuevos clientes.")
        if not form_data.get('razon_social_r'):
            errors.append("Razón Social es obligatoria para nuevos clientes.")
        if not form_data.get('tipo_identificacion_r'):
            errors.append("Tipo de Identificación es obligatorio para nuevos clientes.")
        if not form_data.get('email_r'):
            errors.append("Email es obligatorio para nuevos clientes.")
        if not form_data.get('telefono_r'):
            errors.append("Teléfono es obligatorio para nuevos clientes.")
        # Validar dirección para nuevos clientes
        if not form_data.get('direccion_r_linea1'):
            errors.append("La dirección es obligatoria para nuevos clientes.")
        if not form_data.get('direccion_r_ciudad'):
            errors.append("La ciudad es obligatoria para nuevos clientes.")
        if not form_data.get('direccion_r_departamento'):
            errors.append("El departamento es obligatorio para nuevos clientes.")
        if not form_data.get('direccion_r_pais'):
            errors.append("El país es obligatorio para nuevos clientes.") 

    if not form_data.get('despacho_tipo'):
        errors.append("El Tipo de Despacho es obligatorio.")
    elif form_data.get('despacho_tipo') == 'DOMICILIO':  # Usar los mismos valores que el picklist
        # Verificar que los campos de dirección de entrega estén completos
        if not form_data.get('direccion_entrega'):
            errors.append("La dirección de entrega es obligatoria para Domicilio.")
        if not form_data.get('ciudad_entrega'):
            errors.append("La ciudad de entrega es obligatoria para Domicilio.")
        if not form_data.get('departamento_entrega'):
            errors.append("El departamento de entrega es obligatorio para Domicilio.")

    pedido_items = form_data.get('pedido_items', [])
    
    # DEBUG TEMPORAL: Ver qué datos llegan
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"🔍 DEBUG PEDIDO_ITEMS: {pedido_items}")
    logger.warning(f"🔍 DEBUG FORM_DATA keys: {list(form_data.keys())}")
    
    # Debug específico de campos cantidad
    cantidad_keys = [k for k in form_data.keys() if 'cantidad' in k]
    for key in cantidad_keys:
        logger.warning(f"🔍 DEBUG FORM_DATA['{key}'] = '{form_data[key]}'")
    
    if not pedido_items:
        errors.append("Debe agregar al menos un producto al pedido.")
    else:
        fecha_minima_entrega = calcular_fecha_minima_entrega()
        
        for i, item in enumerate(pedido_items):
            if not item.get('producto_id'):
                errors.append(f"Ítem {i+1}: Debe seleccionar un producto.")
            if not item.get('cantidad') or int(item.get('cantidad', 0)) <= 0:  # CAMBIADO: usar int() en lugar de float()
                errors.append(f"Ítem {i+1}: La cantidad debe ser mayor que cero.")
            if not item.get('fecha_de_entrega_item'):
                errors.append(f"Ítem {i+1}: La fecha de entrega es obligatoria.")
            
            # Validar que la fecha de entrega sea una fecha válida (formato YYYY-MM-DD)
            # NOTA: La validación de fecha mínima se removió porque ahora se calcula automáticamente
            try:
                if item.get('fecha_de_entrega_item'):
                    fecha_entrega = datetime.date.fromisoformat(item.get('fecha_de_entrega_item'))
                    # Comentado: Ya no validamos fecha mínima porque se calcula automáticamente
                    # if fecha_entrega < fecha_minima_entrega:
                    #     errors.append(f"Ítem {i+1}: La fecha de entrega debe ser al menos {fecha_minima_entrega.strftime('%d/%m/%Y')} (2 días hábiles desde hoy).")
            except ValueError:
                errors.append(f"Ítem {i+1}: Formato de fecha de entrega inválido. Usar YYYY-MM-DD.")

    return errors

def guardar_pedido_completo(db: Session, form_data: dict) -> tuple:
    """
    Valida y guarda un nuevo pedido, creando un cliente si es necesario.
    Combina la lógica de 'Paso 3. Crear Nuevo Client' y el guardado del pedido.

    Args:
        db: Sesión de SQLAlchemy.
        form_data: Diccionario con los datos del formulario.

    Returns:
        tuple: (success: bool, data: int | list)
                 Si success es True, data es el ID del pedido creado.
                 Si success es False, data es la lista de errores de validación.
    """
    validation_errors = validar_datos_pedido(form_data)
    if validation_errors:
        return False, validation_errors

    cliente_id_para_pedido = None
    numero_identificacion_cliente = form_data.get('numero_identificacion_cliente_ingresado')

    # Buscar cliente por número de identificación ingresado
    cliente_existente = db.query(Cliente).filter(Cliente.numero_identificacion == numero_identificacion_cliente).first()

    # PASO 1: CREAR O UBICAR CLIENTE (si es necesario)
    if form_data.get('show_seccion_registro') and not cliente_existente:
        # Si se muestra la sección de registro y no existe el cliente, crear un nuevo cliente
        # Primero verificamos que tengamos los campos obligatorios
        if not form_data.get('nombre_comercial_r') or not form_data.get('tipo_identificacion_r'):
            return False, ["Información de cliente incompleta. Por favor complete todos los campos requeridos."]
        
        # Usar el número de identificación del formulario principal si el campo de registro está vacío
        numero_identificacion_registro = form_data.get('numero_identificacion_r')
        if not numero_identificacion_registro:
            numero_identificacion_registro = numero_identificacion_cliente
            
        try:
            # Crear nuevo cliente en una transacción independiente
            nuevo_cliente = Cliente(
                nombre_comercial=form_data.get('nombre_comercial_r'),
                razon_social=form_data.get('razon_social_r'),
                tipo_identificacion=form_data.get('tipo_identificacion_r'),
                numero_identificacion=numero_identificacion_registro,
                email=form_data.get('email_r'),
                telefono=form_data.get('telefono_r'),
                direccion_linea1=form_data.get('direccion_r_linea1'),
                direccion_linea2=form_data.get('direccion_r_linea2'),
                direccion_ciudad=form_data.get('direccion_r_ciudad'),
                direccion_departamento=form_data.get('direccion_r_departamento'),
                direccion_codigo_postal=form_data.get('direccion_r_codigo_postal'),
                direccion_pais=form_data.get('direccion_r_pais')
            )
            db.add(nuevo_cliente)
            db.commit()
            db.refresh(nuevo_cliente)
            cliente_id_para_pedido = nuevo_cliente.id
            
            # Verificar que efectivamente se guardó el cliente
            cliente_guardado = db.query(Cliente).get(nuevo_cliente.id)
            if not cliente_guardado:
                return False, ["Error: El cliente se creó pero no se pudo recuperar de la base de datos."]
                
            # Ahora que tenemos el cliente guardado, lo asignamos a cliente_existente
            cliente_existente = cliente_guardado
            
        except Exception as e:
            db.rollback()
            return False, [f"Error al crear el cliente: {str(e)}"]
    elif cliente_existente:
        cliente_id_para_pedido = cliente_existente.id
    else:
        return False, ["Error: No se pudo determinar el cliente para el pedido. Verifique el número de identificación."]

    # PASO 2: CREAR PEDIDO (usando el cliente ya confirmado)
    try:
        # Crear el Pedido en una nueva transacción
        nuevo_pedido = Pedido(
            numero_identificacion_cliente_ingresado=numero_identificacion_cliente,
            nombre_cliente_ingresado=form_data.get('nombre_cliente_ingresado') if form_data.get('nombre_cliente_ingresado') else cliente_existente.nombre_comercial,
            cliente_id=cliente_id_para_pedido,
            alerta=form_data.get('alerta_value'),
            despacho_tipo=form_data.get('despacho_tipo'),
            despacho_sede=form_data.get('despacho_sede'),
            direccion_entrega=form_data.get('direccion_entrega'),
            ciudad_entrega=form_data.get('ciudad_entrega'),
            departamento_entrega=form_data.get('departamento_entrega'),
            despacho_horario_atencion=form_data.get('despacho_horario_atencion'),
            observaciones_despacho=form_data.get('despacho_observaciones'),
            estado_pedido_general=form_data.get('estado_pedido_general', 'En Proceso')
        )

        # Crear los PedidoProducto (items del pedido)
        for item_data in form_data.get('pedido_items', []):
            # Convertir fecha de string a objeto date si no está vacía
            fecha_entrega_obj = None
            if item_data.get('fecha_de_entrega_item'):
                try:
                    fecha_entrega_obj = datetime.date.fromisoformat(item_data.get('fecha_de_entrega_item'))
                except ValueError:
                    # Si la fecha no es válida, dejarla como None
                    fecha_entrega_obj = None
            
            # AGREGADO: Calcular fecha_pedido_item (fecha cuando se hace el pedido - hoy)
            fecha_pedido_item = datetime.date.today()
            
            pedido_producto = PedidoProducto(
                producto_id=item_data.get('producto_id'),
                fecha_pedido_item=fecha_pedido_item,  # AGREGADO: Columna faltante
                cantidad=int(item_data.get('cantidad')),  # CAMBIADO: De float a int
                gramaje_g_item=float(item_data.get('gramaje_g_item')),
                peso_total_g_item=float(item_data.get('peso_total_g_item')),
                grupo_item=item_data.get('grupo_item'),
                linea_item=item_data.get('linea_item'),
                comentarios_item=item_data.get('comentarios_item'),  # CAMBIADO: De observaciones_item a comentarios_item
                fecha_de_entrega_item=fecha_entrega_obj,
                estado_del_pedido_item=item_data.get('estado_del_pedido_item', 'Pendiente')
            )
            nuevo_pedido.items.append(pedido_producto)
        
        db.add(nuevo_pedido)
        db.commit()
        db.refresh(nuevo_pedido)
        return True, nuevo_pedido.id
    except Exception as e:
        db.rollback()
        return False, [f"Error al guardar el pedido: {str(e)}"]

def actualizar_estado_items_pedido(db: Session, pedido_id: int, nuevo_estado_general: str) -> bool:
    """
    Actualiza el campo 'estado_del_pedido_item' de todos los ítems de un pedido
    cuando el 'estado_pedido_general' del pedido cambia.
    Corresponde a la lógica de 'Estado_del_Pedido_Cambio_' en Deluge.

    Args:
        db: Sesión de SQLAlchemy.
        pedido_id: El ID del pedido cuyo estado general ha cambiado.
        nuevo_estado_general: El nuevo estado general que se aplicará a los ítems.

    Returns:
        bool: True si la actualización fue exitosa, False en caso contrario.
    """
    try:
        pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
        if not pedido:
            print(f"Error: Pedido con ID {pedido_id} no encontrado.")
            return False

        for item in pedido.items: # type: ignore
            item.estado_del_pedido_item = nuevo_estado_general
        
        # Es importante también actualizar el estado general del pedido mismo.
        # La lógica de Deluge parece implicar que el cambio en el campo del formulario Pedidos
        # es lo que dispara esta acción, por lo que el estado del Pedido principal ya estaría
        # siendo actualizado por la UI/controlador antes de llamar a esta función específica para los items.
        # Si esta función es el ÚNICO lugar donde se actualiza el estado, entonces también deberías hacer:
        # pedido.estado_pedido_general = nuevo_estado_general
        
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Error al actualizar el estado de los ítems del pedido: {e}")
        return False

# --- Lógica para importar productos desde Excel ---
# Necesitarás instalar la librería openpyxl: pip install openpyxl
import openpyxl

def importar_productos_desde_excel(db: Session, archivo_excel_path: str) -> tuple:
    """
    Importa productos a la base de datos desde un archivo Excel.
    Espera columnas específicas en el archivo Excel:
    'Codigo', 'Referencia de Producto', 'Gramaje (g)', 'Formulacion/Grupo', 'Categoria/Linea'

    Args:
        db: Sesión de SQLAlchemy.
        archivo_excel_path: Ruta al archivo Excel (.xlsx).

    Returns:
        tuple: (success: bool, message: str, importados: int, actualizados: int, errores: list)
    """
    importados_count = 0
    actualizados_count = 0
    errores_list = []

    try:
        workbook = openpyxl.load_workbook(archivo_excel_path)
        sheet = workbook.active # Asume que los datos están en la primera hoja activa

        # Asumir que la primera fila es de encabezados
        headers = [cell.value for cell in sheet[1]]
        # Mapeo esperado de encabezados (sensible a mayúsculas/minúsculas tal como está)
        # Podrías hacerlo insensible a mayúsculas/minúsculas y normalizar espacios si es necesario
        expected_headers = {
            'Codigo': 'codigo',
            'Referencia de Producto': 'referencia_de_producto',
            'Gramaje (g)': 'gramaje_g',
            'Formulacion/Grupo': 'formulacion_grupo',
            'Categoria/Linea': 'categoria_linea'
        }
        
        # Validar encabezados
        column_map = {}
        for expected_header, model_field in expected_headers.items():
            try:
                column_map[model_field] = headers.index(expected_header)
            except ValueError:
                errores_list.append(f"Encabezado esperado no encontrado: '{expected_header}'")
        
        if errores_list: # Si faltan encabezados cruciales, no continuar
            return False, "Error en encabezados del Excel.", 0, 0, errores_list

        for row_idx, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
            if not any(row): # Omitir filas completamente vacías
                continue

            try:
                codigo = row[column_map['codigo']]
                if not codigo:
                    errores_list.append(f"Fila {row_idx}: El campo 'Codigo' es obligatorio.")
                    continue
                
                referencia = row[column_map['referencia_de_producto']]
                if not referencia:
                    errores_list.append(f"Fila {row_idx}, Código '{codigo}': El campo 'Referencia de Producto' es obligatorio.")
                    continue

                try:
                    gramaje_str = str(row[column_map['gramaje_g']])
                    if not gramaje_str:
                         errores_list.append(f"Fila {row_idx}, Código '{codigo}': El campo 'Gramaje (g)' es obligatorio.")
                         continue
                    gramaje = float(gramaje_str)
                    if gramaje <= 0:
                        errores_list.append(f"Fila {row_idx}, Código '{codigo}': El gramaje debe ser un número positivo.")
                        continue
                except (ValueError, TypeError):
                    errores_list.append(f"Fila {row_idx}, Código '{codigo}': Valor inválido para 'Gramaje (g)'. Debe ser un número.")
                    continue

                formulacion = row[column_map['formulacion_grupo']]
                categoria = row[column_map['categoria_linea']]

                # Buscar si el producto ya existe por código
                producto_existente = db.query(Producto).filter(Producto.codigo == str(codigo)).first()

                if producto_existente:
                    # Actualizar producto existente
                    producto_existente.referencia_de_producto = referencia
                    producto_existente.gramaje_g = gramaje
                    producto_existente.formulacion_grupo = formulacion
                    producto_existente.categoria_linea = categoria
                    actualizados_count += 1
                else:
                    # Crear nuevo producto
                    nuevo_producto = Producto(
                        codigo=str(codigo),
                        referencia_de_producto=referencia,
                        gramaje_g=gramaje,
                        formulacion_grupo=formulacion,
                        categoria_linea=categoria
                    )
                    db.add(nuevo_producto)
                    importados_count += 1
            
            except IndexError:
                 errores_list.append(f"Fila {row_idx}: Número incorrecto de columnas o datos faltantes.")
                 continue # Saltar a la siguiente fila
            except Exception as e:
                errores_list.append(f"Fila {row_idx}, Código '{codigo if 'codigo' in locals() else 'desconocido'}': Error inesperado - {str(e)}")
                continue

        db.commit()
        if not errores_list:
            return True, "Importación completada exitosamente.", importados_count, actualizados_count, []
        else:
            return True, f"Importación completada con {len(errores_list)} errores.", importados_count, actualizados_count, errores_list

    except FileNotFoundError:
        return False, f"Archivo no encontrado: {archivo_excel_path}", 0, 0, [f"Archivo no encontrado: {archivo_excel_path}"]
    except Exception as e:
        db.rollback()
        return False, f"Error durante la importación: {str(e)}", 0, 0, [f"Error general: {str(e)}"]

# Caché simple para productos (evita consultas repetitivas)
_productos_cache = None
_cache_timestamp = None
CACHE_DURATION = 300  # 5 minutos en segundos

def get_productos_cached(db):
    """Obtiene productos desde caché o base de datos"""
    global _productos_cache, _cache_timestamp
    import time
    
    current_time = time.time()
    
    # Verificar si el caché es válido
    if (_productos_cache is None or 
        _cache_timestamp is None or 
        (current_time - _cache_timestamp) > CACHE_DURATION):
        
        # Actualizar caché
        productos = db.query(Producto).all()
        _productos_cache = [
            {
                "id": p.id,
                "codigo": p.codigo,
                "referencia_de_producto": p.referencia_de_producto,
                "gramaje_g": p.gramaje_g,
                "formulacion_grupo": p.formulacion_grupo,
                "categoria_linea": p.categoria_linea
            }
            for p in productos
        ]
        _cache_timestamp = current_time
        
        if os.getenv('FLASK_ENV') != 'production':
            logger.info(f"Caché de productos actualizado: {len(_productos_cache)} productos")
    
    return _productos_cache

def invalidate_productos_cache():
    """Invalida el caché de productos"""
    global _productos_cache, _cache_timestamp
    _productos_cache = None
    _cache_timestamp = None

def calcular_fecha_minima_entrega(fecha_base=None):
    """
    Calcula la fecha mínima de entrega sumando 2 días hábiles a la fecha base.
    
    Args:
        fecha_base: Fecha desde la cual calcular. Si es None, usa la fecha actual.
    
    Returns:
        date: Fecha mínima de entrega
    """
    if fecha_base is None:
        fecha_base = date.today()
    
    dias_sumados = 0
    fecha_resultado = fecha_base
    
    while dias_sumados < 2:
        fecha_resultado += timedelta(days=1)
        # Solo contar días de lunes a sábado (0=lunes, 6=domingo)
        if fecha_resultado.weekday() < 6:  # 0-5 son días laborables (lunes a sábado)
            dias_sumados += 1
    
    return fecha_resultado

