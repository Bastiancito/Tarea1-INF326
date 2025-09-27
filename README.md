## Tarea 1- INF326 - “Arquitectura de Software” 
Autores
* Bastían Camus 202173013-3
* Esteban Castillo
* Matías Fernández 202173108-3
## Instrucciones ejecución de tarea:

1-Se deben buildear las imagenes de docker:

docker compose up -d --build api

2-Para publicar un msj de prueba:

En el codigo de la tarea, hay una variable que tiene guardados distintos ejemplos de sismos, desarrollamos una api que publica de manera aleatoria algunos de estos sismos.

POST : http://localhost:8000/quakes/publish

Esta api retorna un json que indica el sismo publicado, junto a la informacion de este, e informa que regiones ignoraron el sismo y que regiones les intereso debido a su cercania menor a 500km.

Cada subscriber esta constantemente escuchando si la api publica un sismo en las colas de RabbitMQ, y retornan un log  en docker señalando si ignoraron un sismo, o es de interes.

3-Para mirar los logs de cada subscriber de docker en una consola, ejecutar el siguiente comando:

docker compose logs -f sub_arica sub_coquimbo sub_valparaiso sub_concepcion sub_punta_arenas

4-Tambien se puede ver la informacion detallada de todos los sismos que han sido informados a las siguientes regiones, indicando si han sido de interes,ignorados y cuales son especificamente con la ruta:

GET : http://localhost:8000/regions/totals

O bien, para ver los logs en tiempo real, se puede monitorear los logs de la imagen de docker de cualquiera de los subscribers levantados.


