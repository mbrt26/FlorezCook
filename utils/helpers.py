from datetime import datetime

def get_current_year():
    """Obtiene el año actual"""
    return datetime.now().year

def format_currency(amount):
    """Formatea un monto como moneda colombiana"""
    if amount is None:
        return "$0"
    return f"${amount:,.0f}".replace(",", ".")

def safe_float(value, default=0.0):
    """Convierte un valor a float de forma segura"""
    try:
        return float(value) if value else default
    except (ValueError, TypeError):
        return default

def safe_int(value, default=0):
    """Convierte un valor a int de forma segura"""
    try:
        return int(value) if value else default
    except (ValueError, TypeError):
        return default

# Datos de departamentos y ciudades de Colombia
DEPARTAMENTOS_CIUDADES = {
    'Amazonas': ['Leticia', 'Puerto Nariño'],
    'Antioquia': ['Medellín', 'Bello', 'Itagüí', 'Envigado', 'Apartadó', 'Turbo', 'Rionegro', 'Sabaneta', 'La Estrella', 'Copacabana'],
    'Arauca': ['Arauca', 'Tame', 'Saravena', 'Fortul', 'Puerto Rondón', 'Cravo Norte', 'Arauquita'],
    'Atlántico': ['Barranquilla', 'Soledad', 'Malambo', 'Sabanagrande', 'Puerto Colombia', 'Galapa', 'Palmar de Varela'],
    'Bolívar': ['Cartagena', 'Magangué', 'Turbaco', 'Arjona', 'El Carmen de Bolívar', 'San Pablo', 'Mompox'],
    'Boyacá': ['Tunja', 'Duitama', 'Sogamoso', 'Chiquinquirá', 'Paipa', 'Villa de Leyva', 'Puerto Boyacá'],
    'Caldas': ['Manizales', 'La Dorada', 'Chinchiná', 'Riosucio', 'Anserma', 'Villamaría', 'Palestina'],
    'Caquetá': ['Florencia', 'San Vicente del Caguán', 'Puerto Rico', 'La Montañita', 'Curillo', 'El Paujil'],
    'Casanare': ['Yopal', 'Aguazul', 'Villanueva', 'Tauramena', 'Monterrey', 'Paz de Ariporo'],
    'Cauca': ['Popayán', 'Santander de Quilichao', 'Puerto Tejada', 'Patía', 'Guapi', 'Corinto'],
    'Cesar': ['Valledupar', 'Aguachica', 'Bosconia', 'Codazzi', 'La Jagua de Ibirico', 'Chiriguaná'],
    'Chocó': ['Quibdó', 'Istmina', 'Condoto', 'Tadó', 'Acandí', 'Capurganá'],
    'Córdoba': ['Montería', 'Lorica', 'Cereté', 'Sahagún', 'Planeta Rica', 'Montelíbano'],
    'Cundinamarca': ['Bogotá', 'Soacha', 'Girardot', 'Zipaquirá', 'Facatativá', 'Chía', 'Mosquera', 'Madrid', 'Funza', 'Cajicá'],
    'Guainía': ['Inírida'],
    'Guaviare': ['San José del Guaviare', 'Calamar', 'El Retorno', 'Miraflores'],
    'Huila': ['Neiva', 'Pitalito', 'Garzón', 'La Plata', 'Campoalegre', 'Timaná'],
    'La Guajira': ['Riohacha', 'Maicao', 'Uribia', 'Manaure', 'San Juan del Cesar', 'Villanueva'],
    'Magdalena': ['Santa Marta', 'Ciénaga', 'Fundación', 'Aracataca', 'El Banco', 'Plato'],
    'Meta': ['Villavicencio', 'Acacías', 'Granada', 'Puerto López', 'Cumaral', 'San Martín'],
    'Nariño': ['Pasto', 'Tumaco', 'Ipiales', 'Túquerres', 'Samaniego', 'La Unión'],
    'Norte de Santander': ['Cúcuta', 'Villa del Rosario', 'Los Patios', 'Ocaña', 'Pamplona', 'Tibú'],
    'Putumayo': ['Mocoa', 'Puerto Asís', 'Orito', 'Valle del Guamuez', 'San Miguel', 'Villagarzón'],
    'Quindío': ['Armenia', 'Calarcá', 'La Tebaida', 'Montenegro', 'Quimbaya', 'Circasia'],
    'Risaralda': ['Pereira', 'Dosquebradas', 'Santa Rosa de Cabal', 'La Virginia', 'Marsella', 'Belén de Umbría'],
    'San Andrés y Providencia': ['San Andrés', 'Providencia'],
    'Santander': ['Bucaramanga', 'Floridablanca', 'Girón', 'Piedecuesta', 'Barrancabermeja', 'San Gil'],
    'Sucre': ['Sincelejo', 'Corozal', 'Sampués', 'San Marcos', 'Tolú', 'Coveñas'],
    'Tolima': ['Ibagué', 'Espinal', 'Melgar', 'Honda', 'Chaparral', 'Líbano'],
    'Valle del Cauca': ['Cali', 'Palmira', 'Buenaventura', 'Tuluá', 'Cartago', 'Buga', 'Jamundí', 'Yumbo'],
    'Vaupés': ['Mitú'],
    'Vichada': ['Puerto Carreño', 'La Primavera', 'Santa Rosalía', 'Cumaribo']
}