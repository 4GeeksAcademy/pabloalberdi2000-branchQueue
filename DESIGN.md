# Diseno de Arquitectura: BranchQueue

## Objetivo
BranchQueue resuelve la gestion de turnos de una sucursal bancaria con tres servicios: deposito, retiro y gestion_cuenta, garantizando:
1. Secuencia global unica de tickets.
2. Orden FIFO por servicio.
3. Comportamiento consistente bajo concurrencia.

Toda la solucion esta basada exclusivamente en biblioteca estandar de Python.

## Restriccion tecnologica
La implementacion se apoya solo en modulos estandar:
1. collections.deque para colas FIFO eficientes.
2. datetime para trazabilidad temporal de emision.
3. typing para contratos de tipos y claridad semantica.
4. threading para sincronizacion en escenarios multiagente.

No se utilizan dependencias de terceros.

## 1. Eficiencia algoritmica y estructura de datos

### Decision de diseno
Se utiliza una cola independiente por tipo de servicio, modelada como un diccionario de deques, en lugar de una cola unica compartida para todos los tickets.

### Comparativa de complejidad
Con colas separadas:
1. call_next(service_type) opera sobre la cabeza de la cola especifica.
2. Extraccion con popleft en deque: O(1).
3. Busqueda adicional: no requerida.

Con cola unica compartida:
1. call_next(service_type) debe localizar el primer ticket del servicio solicitado.
2. Esa localizacion implica iteracion o filtrado sobre la coleccion global.
3. Costo en peor caso: O(N), donde N es el total de tickets en espera.

### Impacto en rendimiento y escalabilidad
Con alta demanda:
1. El enfoque de cola unica degrada linealmente y aumenta latencia por operacion.
2. El enfoque de colas separadas mantiene latencia practicamente constante por servicio.
3. El throughput mejora porque cada atencion evita recorridos globales.
4. La escalabilidad es mas predecible al crecer el volumen total de clientes.

Conclusion: segmentar por servicio transforma la operacion critica de atencion desde O(N) a O(1), con mejora sustancial en tiempos de respuesta y estabilidad operativa.

## 2. Concurrencia, race conditions y mutacion de estado

### Riesgo al llamar call_next en simultaneo
Si dos agentes del mismo servicio ejecutan call_next al mismo tiempo sin sincronizacion:
1. Ambos pueden observar la cola como no vacia.
2. Ambos pueden leer el mismo ticket candidato.
3. Se produce condicion de carrera.
4. Resultado posible: double-calling del mismo cliente o inconsistencia de estado.

### Orden correcto de mutacion atomica
Para evitar double-calling, el orden debe ser estricto:
1. Entrar en seccion critica protegida.
2. Verificar disponibilidad de elementos.
3. Remover el ticket de la cola, o marcarlo como procesado, dentro de la misma seccion critica.
4. Salir de la seccion critica.
5. Retornar datos y notificar al agente despues de la mutacion.

Regla clave: primero mutar estado compartido, despues exponer el resultado al exterior.

### Sincronizacion con biblioteca estandar
Se recomienda sincronizar operaciones compuestas con threading.Lock:
1. Opcion simple: lock global para todas las colas.
2. Opcion de mayor paralelismo: lock por servicio para reducir contencion entre colas independientes.
3. En ambos casos, la unidad atomica debe incluir validacion de no vacio y extraccion.

Patron de operacion segura:
1. acquire lock
2. validar cola
3. popleft o marcar procesado
4. release lock
5. retornar ticket

Este patron evita lecturas concurrentes inconsistentes y garantiza que cada cliente sea llamado como maximo una vez.

## Decisiones finales
1. Estructura principal: diccionario de deques por servicio.
2. Operacion critica call_next: extraccion directa O(1) por cola.
3. Concurrencia: seccion critica con locking en mutaciones de cola.
4. Correctitud: mutacion primero, notificacion despues.

Esta arquitectura equilibra simplicidad, eficiencia y seguridad concurrente usando unicamente capacidades nativas de Python.
