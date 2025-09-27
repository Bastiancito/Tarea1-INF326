import os

AMQP_HOST = os.getenv("AMQP_HOST", "rabbitmq")
AMQP_PORT = int(os.getenv("AMQP_PORT", "5672"))
AMQP_USER = os.getenv("AMQP_USER", "guest")
AMQP_PASS = os.getenv("AMQP_PASS", "guest")
AMQP_QUEUE = os.getenv("AMQP_QUEUE", "quakes")

EXCHANGE_NAME = "quakes"

MGMT_PORT = int(os.getenv("AMQP_MANAGEMENT_PORT", "15672"))
MGMT_USER = AMQP_USER
MGMT_PASS = AMQP_PASS

UMBRAL_KM = float(os.getenv("UMBRAL_KM", "500"))

SUBSCRIBERS = {
    "Arica": {"lat": -18.4746, "lon": -70.29792},
    "Coquimbo": {"lat": -29.95332, "lon": -71.33947},
    "Valparaíso": {"lat": -33.036, "lon": -71.62963},
    "Concepción": {"lat": -36.82699, "lon": -73.04977},
    "Punta Arenas": {"lat": -53.16282, "lon": -70.90922},
}
