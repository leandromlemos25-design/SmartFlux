from __future__ import annotations

import logging
from typing import Any, Mapping, Optional

from shopee_price_guard import PriceValidationError, build_telegram_caption, validate_shopee_offer


log = logging.getLogger(__name__)


async def publish_shopee_offer(
    bot: Any,
    chat_id: int | str,
    node: Mapping[str, Any],
    *,
    user_request: Optional[str] = None,
    search_term: Optional[str] = None,
) -> bool:
    """Validate one Shopee productOfferV2 node before sending it to Telegram."""
    try:
        offer = validate_shopee_offer(node, user_request=user_request, search_term=search_term)
    except PriceValidationError as exc:
        log.warning(
            "Oferta bloqueada por preco inseguro: %s | item=%r | titulo=%r | priceMin=%r | priceMax=%r | commission=%r",
            exc,
            node.get("itemId") or node.get("productId"),
            node.get("productName") or node.get("title"),
            node.get("priceMin"),
            node.get("priceMax"),
            node.get("commission"),
        )
        return False

    caption = build_telegram_caption(offer)

    if offer.image_url:
        await bot.send_photo(
            chat_id=chat_id,
            photo=offer.image_url,
            caption=caption,
            parse_mode="HTML",
            disable_web_page_preview=False,
        )
    else:
        await bot.send_message(
            chat_id=chat_id,
            text=caption,
            parse_mode="HTML",
            disable_web_page_preview=False,
        )

    return True


async def answer_private_request(
    bot: Any,
    user_chat_id: int | str,
    node: Mapping[str, Any],
    *,
    user_request: Optional[str] = None,
    search_term: Optional[str] = None,
) -> bool:
    """Use the same guard for private chat requests."""
    return await publish_shopee_offer(bot, user_chat_id, node, user_request=user_request, search_term=search_term)


async def publish_group_batch(bot: Any, group_chat_id: int | str, nodes: list[Mapping[str, Any]]) -> int:
    """Post only validated offers and return how many were sent."""
    sent = 0
    for node in nodes:
        if await publish_shopee_offer(bot, group_chat_id, node):
            sent += 1
    return sent
