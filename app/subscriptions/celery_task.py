from kombu import Queue, Exchange

subscriptions_exchange = Exchange(name="subscriptions", type="direct")
subscriptions_queue = Queue(
    name="subscriptions",
    exchange=subscriptions_exchange,
    routing_key="subscriptions",
)
