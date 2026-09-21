"""Side-effect notifications, isolated from controllers.

Uses structured logging instead of print(); swapping to a real provider later
only touches this module.
"""
import logging

logger = logging.getLogger("notifications")


def notify_order_created(pedido_id, usuario_id):
    logger.info("order.created", extra={"pedido_id": pedido_id, "usuario_id": usuario_id})
    # Placeholders for real channels (email/SMS/push) — kept out of the controller.


def notify_status_change(pedido_id, novo_status):
    if novo_status == "aprovado":
        logger.info("order.approved", extra={"pedido_id": pedido_id})
    elif novo_status == "cancelado":
        logger.info("order.cancelled", extra={"pedido_id": pedido_id})
