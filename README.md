## Tarea 1- INF326 - “Arquitectura de Software” 

1-Para buildear las imagenes en docker:

docker compose up -d --build

2-Para publicar un msj de prueba:

docker compose exec app python -m messaging.publisher

3-Para ver los logs de todos los subs, mirar logs de cada subscriber en docker o ejecutar el siguiente comando en consola:

docker compose logs -f sub_arica sub_coquimbo sub_valparaiso sub_concepcion sub_punta_arenas


## Discusión de Trade-offs en la Arquitectura 

La arquitectura usa **publish–subscribe** con RabbitMQ y un **modelo pull** hacia el API:

- **Desacoplamiento vs. complejidad:** Permite agregar/quitar ciudades fácilmente, pero requiere operar un broker adicional.  
- **Escalabilidad:** Escala bien con más suscriptores; sin embargo, un único broker puede ser cuello de botella en picos de eventos.  
- **Modelo pull:** Reduce carga al API (solo consultan los interesados), pero lo hace crítico: si el API cae, no hay detalles.  
- **Persistencia:** Usar datos en memoria simplifica, pero implica pérdida ante reinicios; en producción se necesitaría una base de datos.  

**En este dominio (notificación de sismos),** la rapidez y la tolerancia a fallos son prioritarias. El desacoplamiento y la capacidad de escalar pesan más que la simplicidad de la implementación, aunque habría que reforzar persistencia y alta disponibilidad en un escenario real.

---

## Discusión sobre “Back of the Envelope” 

El “Back of the Envelope” se puede usar para hacer cuentas rápidas que ayuden a estimar si la arquitectura soporta el uso esperado.

**Cómo lo aplicaría en este sistema:**
- Revisar cuántos sismos ocurren en promedio en Chile y en los momentos de mayor actividad (enjambres).
- Calcular, de forma aproximada, cuántos mensajes se enviarían a los suscriptores por cada sismo.
- Estimar cuántas consultas al API se generarían, considerando que solo se hacen si el sismo está a menos de 500 km de una ciudad.
- Con esas cifras, pensar si un solo broker de RabbitMQ y un API en memoria son suficientes, o si habría que escalar a más instancias, usar base de datos o balanceo de carga.

**En resumen:** con estos cálculos rápidos puedo justificar que la arquitectura actual es adecuada para el volumen esperado, y también identificar en qué punto sería necesario reforzarla si la cantidad de sismos o suscriptores creciera mucho.

