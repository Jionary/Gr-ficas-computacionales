Simulación de Tráfico con Semáforos Inteligentes
Un sistema de simulación multiagente que modela el flujo de tráfico y el comportamiento de semáforos inteligentes utilizando Mesa 3.0.3 y Unity para la visualización. El proyecto simula la dinámica del tráfico en intersecciones urbanas con gestión inteligente del tráfico.

Características
Semáforos inteligentes que se adaptan a las condiciones del tráfico
Múltiples agentes vehiculares con diferentes comportamientos
Visualización en tiempo real en Unity
Optimización del flujo de tráfico
Métricas de felicidad para vehículos
Soporte para múltiples carriles
Sistema de comunicación descentralizado
Requisitos
Python 3.8+
Mesa 3.0.3
Unity 2021.3 o posterior
Flask (para la comunicación Unity-Python)
Instalación
Instalar Mesa 3.0.3: bash pip install mesa==3.0.3

Instalar dependencias adicionales: bash pip install flask numpy pandas matplotlib

Clonar el repositorio: bash git clone [url-del-repositorio] cd [nombre-del-repositorio]

Abrir el proyecto en Unity:

Navegar a la carpeta unity_visualization
Abrir el proyecto en Unity Hub
Estructura del Proyecto
model.py: Contiene el modelo principal de simulación
server.py: Maneja la comunicación entre Mesa y Unity
movements.py: Define las reglas de movimiento de los agentes
flask.py: Implementación de API para la integración con Unity
unity_visualization/: Archivos del proyecto Unity para visualización 3D
Ejecutar la Simulación
Iniciar el servidor Flask: bash python server.py

Abrir la escena de Unity y presionar Play

La simulación comenzará con vehículos apareciendo y semáforos operando según las reglas definidas

Componentes Principales
Semáforos Inteligentes: Se adaptan a las condiciones del tráfico
Vehículos: Agentes autónomos con comportamientos personalizables
Puntos de Generación: Crean vehículos con diferentes parámetros
Edificios: Obstáculos estáticos que definen el entorno urbano
Equipo
David Alberto Padrón Sánchez
Santiago Calderón Ortega
Jesús Jionary Gutiérrez Moreno
Carlos Anaya Ruiz
Sebastián Reyes Moguel
Documentación
Para información más detallada sobre la arquitectura del proyecto y detalles de implementación, consulte la documentación del proyecto.

Notas Adicionales
El proyecto utiliza un enfoque descentralizado para la gestión del tráfico
Las métricas y gráficas están disponibles para análisis de rendimiento
Los agentes pueden adaptarse a diferentes condiciones de tráfico
La visualización en Unity permite una mejor comprensión del comportamiento del sistema
Problemas Comunes
Si encuentra problemas al ejecutar la simulación:

Verificar que todas las dependencias estén instaladas correctamente
Asegurarse de que el servidor Flask esté corriendo antes de iniciar Unity
Comprobar las versiones de Python y Mesa sean las correctas
Revisar la conexión entre Flask y Unity si la visualización no funciona
