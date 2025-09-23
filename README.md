1-Para buildear las imagenes en docker:

docker compose up -d --build

2-Para publicar un msj de prueba:

docker compose exec app python -m messaging.publisher

3-Para ver los logs de todos los subs, mirar logs de cada subscriber en docker o ejecutar el siguiente comando en consola:

docker compose logs -f sub_arica sub_coquimbo sub_valparaiso sub_concepcion sub_punta_arenas