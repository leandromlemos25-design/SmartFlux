from __future__ import annotations

import logging
import math
import re
import unicodedata
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from html import escape
from typing import Any, Mapping, Optional

from offer_intent import detect_product_intent, generic_title_validation_error, title_validation_error


log = logging.getLogger(__name__)

CENT = Decimal("0.01")
MIN_GENERIC_PRICE = Decimal("1.00")
MAX_REASONABLE_PRICE = Decimal("300000.00")
MAX_RANGE_RATIO = Decimal("8")
HIGH_DISCOUNT_LIMIT = Decimal("90")

PRIMARY_PRICE_FIELDS = ("priceMin", "price", "priceMax")

ACCESSORY_RE = re.compile(
    r"\b("
    r"capa|capinha|case|pelicula|vidro|carregador|cabo|fone|"
    r"suporte|adaptador|lente|dock|pulseira|bracelete|controle remoto"
    r")\b",
)

TITLE_PRICE_FLOORS: tuple[tuple[re.Pattern[str], Decimal, str], ...] = (
    (re.compile(r"\b(iphone|ipad|macbook|apple watch)\b"), Decimal("1000.00"), "Apple caro demais para esse preco"),
    (re.compile(r"\b(ar condicionado|condicionado|split|inverter|btus?|btu/h)\b"), Decimal("700.00"), "ar condicionado caro demais para esse preco"),
    (re.compile(r"\b(playstation|ps5|xbox|nintendo switch)\b"), Decimal("900.00"), "console caro demais para esse preco"),
    (re.compile(r"\b(notebook|laptop|ultrabook|computador|desktop|mini\s*pc|all\s*in\s*one|pc gamer|pc completo|computador gamer)\b"), Decimal("800.00"), "computador caro demais para esse preco"),
    (re.compile(r"\b(smart tv|televisao|tv\s+\d{2})\b"), Decimal("450.00"), "TV cara demais para esse preco"),
    (re.compile(r"\bmonitor\b"), Decimal("200.00"), "monitor caro demais para esse preco"),
    (re.compile(r"\b(geladeira|refrigerador|freezer|fogao|lava e seca|lavadora)\b"), Decimal("250.00"), "eletrodomestico caro demais para esse preco"),
    (re.compile(r"\b(celular|smartphone|galaxy s|galaxy z|xiaomi|motorola|samsung)\b"), Decimal("250.00"), "celular caro demais para esse preco"),
)


class PriceValidationError(ValueError):
    """Raised when an offer must not be posted because its price is unsafe."""


@dataclass(frozen=True)
class SafeShopeeOffer:
    item_id: Optional[str]
    title: str
    price_min: Decimal
    price_max: Optional[Decimal]
    discount_percent: Optional[Decimal]
    image_url: Optional[str]
    offer_link: Optional[str]
    product_link: Optional[str]
    shop_name: Optional[str]

    @property
    def price_text(self) -> str:
        if self.price_max and self.price_max > self.price_min:
            return f"{format_brl(self.price_min)} ~ {format_brl(self.price_max)}"
        return format_brl(self.price_min)


def parse_shopee_money(value: Any) -> Optional[Decimal]:
    """Convert Shopee Affiliate money fields to BRL.

    Numeric API values from productOfferV2 are centavos. For example, 275700
    becomes R$ 2.757,00. Already formatted text like "R$ 2.757,00" is parsed
    as text and is not divided again.
    """
    if value is None or isinstance(value, bool):
        return None

    if isinstance(value, int):
        return _quantize(Decimal(value) / 100)

    if isinstance(value, Decimal):
        return _quantize(value)

    if isinstance(value, float):
        if not math.isfinite(value):
            return None
        return _quantize(Decimal(str(value)))

    text = str(value).strip()
    if not text or _normalize_for_search(text) in {"none", "null", "nan", "indisponivel"}:
        return None

    if re.fullmatch(r"\d+", text):
        return _quantize(Decimal(text) / 100)

    normalized = _normalize_money_text(text)
    if normalized is None:
        return None

    try:
        return _quantize(Decimal(normalized))
    except InvalidOperation:
        return None


def validate_shopee_offer(
    node: Mapping[str, Any],
    *,
    min_price_override: Optional[Decimal] = None,
    user_request: Optional[str] = None,
    search_term: Optional[str] = None,
) -> SafeShopeeOffer:
    """Return a safe offer or raise PriceValidationError before Telegram send."""
    title = _first_text(node, "productName", "title", "name", "itemName")
    if not title:
        raise PriceValidationError("Oferta sem titulo de produto.")

    intent_context = " ".join(part for part in (user_request, search_term) if part)
    request_intent = detect_product_intent(intent_context) if intent_context else None
    if request_intent:
        relevance_error = title_validation_error(title, request_intent)
        if relevance_error:
            raise PriceValidationError(f"Resultado bloqueado: {title!r}: {relevance_error}")
    elif intent_context:
        relevance_error = generic_title_validation_error(intent_context, title)
        if relevance_error:
            raise PriceValidationError(f"Resultado bloqueado: {title!r}: {relevance_error}")

    parsed_prices = {field: parse_shopee_money(node.get(field)) for field in PRIMARY_PRICE_FIELDS}

    for field, price in parsed_prices.items():
        if node.get(field) is not None and price is not None and price <= 0:
            raise PriceValidationError(f"Oferta bloqueada: {field} veio zerado ou negativo ({node.get(field)!r}).")

    price_min = parsed_prices.get("priceMin") or parsed_prices.get("price")
    price_max = parsed_prices.get("priceMax")

    if price_min is None:
        if node.get("commission") is not None:
            raise PriceValidationError("Oferta sem priceMin/price. O campo commission nao pode ser usado como preco.")
        raise PriceValidationError("Oferta sem campo de preco valido (priceMin ou price).")

    if not _is_reasonable_money(price_min):
        raise PriceValidationError(f"Preco fora da faixa segura: {format_brl(price_min)}.")

    if price_max is not None:
        if not _is_reasonable_money(price_max):
            raise PriceValidationError(f"Preco maximo fora da faixa segura: {format_brl(price_max)}.")
        if price_max < price_min:
            raise PriceValidationError(
                f"Faixa de preco inconsistente: min={format_brl(price_min)} max={format_brl(price_max)}."
            )
        if price_min > 0 and (price_max / price_min) > MAX_RANGE_RATIO:
            raise PriceValidationError(
                f"Faixa de preco ampla demais para postar com seguranca: {format_brl(price_min)} a {format_brl(price_max)}."
            )

    floor = min_price_override or min_price_for_title(title)
    if request_intent:
        floor = max(floor, request_intent.min_price)
    if price_min < floor:
        raise PriceValidationError(
            f"Preco suspeito para o produto: {title!r} saiu por {format_brl(price_min)}, minimo seguro {format_brl(floor)}."
        )

    discount_percent = parse_percent(node.get("priceDiscountRate"))
    if discount_percent is not None:
        if discount_percent < 0 or discount_percent > 100:
            raise PriceValidationError(f"Desconto invalido: {discount_percent}%.")
        if discount_percent >= HIGH_DISCOUNT_LIMIT and price_min <= Decimal("10.00"):
            raise PriceValidationError(
                f"Desconto alto demais com preco baixo ({discount_percent}% em {format_brl(price_min)})."
            )

    return SafeShopeeOffer(
        item_id=_optional_text(node.get("itemId") or node.get("productId")),
        title=title,
        price_min=price_min,
        price_max=price_max if price_max and price_max > price_min else None,
        discount_percent=discount_percent,
        image_url=_optional_text(node.get("imageUrl") or node.get("image")),
        offer_link=_optional_text(node.get("offerLink")),
        product_link=_optional_text(node.get("productLink") or node.get("link")),
        shop_name=_optional_text(node.get("shopName")),
    )


def min_price_for_title(title: str) -> Decimal:
    normalized_title = _normalize_for_search(title)
    if ACCESSORY_RE.search(normalized_title):
        return MIN_GENERIC_PRICE

    for pattern, floor, _reason in TITLE_PRICE_FLOORS:
        if pattern.search(normalized_title):
            return floor

    return MIN_GENERIC_PRICE


def build_telegram_caption(offer: SafeShopeeOffer) -> str:
    lines = [
        "<b>OFERTA VALIDADA</b>",
        "",
        f"<b>{escape(offer.title)}</b>",
        "",
        f"<b>{escape(offer.price_text)}</b>",
    ]

    if offer.discount_percent is not None and offer.discount_percent > 0:
        lines.append(f"{format_percent(offer.discount_percent)} OFF")

    if offer.shop_name:
        lines.append(escape(offer.shop_name))

    link = offer.offer_link or offer.product_link
    if link:
        lines.extend(["", f'<a href="{escape(link, quote=True)}">COMPRAR COM DESCONTO</a>'])

    return "\n".join(lines)


def format_brl(value: Decimal) -> str:
    amount = _quantize(value)
    text = f"{amount:,.2f}"
    text = text.replace(",", "_").replace(".", ",").replace("_", ".")
    return f"R$ {text}"


def format_percent(value: Decimal) -> str:
    amount = value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP).normalize()
    return str(amount).replace(".", ",")


def parse_percent(value: Any) -> Optional[Decimal]:
    if value is None or isinstance(value, bool):
        return None

    text = str(value).strip().replace("%", "").replace(",", ".")
    if not text:
        return None

    try:
        percent = Decimal(text)
    except InvalidOperation:
        return None

    if Decimal("0") < percent <= Decimal("1"):
        percent *= 100

    return percent.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _is_reasonable_money(value: Decimal) -> bool:
    return MIN_GENERIC_PRICE <= value <= MAX_REASONABLE_PRICE


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def _normalize_money_text(text: str) -> Optional[str]:
    cleaned = text.replace("\xa0", " ")
    cleaned = re.sub(r"[^\d,.\-]", "", cleaned)
    if not cleaned or cleaned in {"-", ".", ","}:
        return None

    if "," in cleaned and "." in cleaned:
        last_comma = cleaned.rfind(",")
        last_dot = cleaned.rfind(".")
        if last_comma > last_dot:
            cleaned = cleaned.replace(".", "").replace(",", ".")
        else:
            cleaned = cleaned.replace(",", "")
        return cleaned

    if "," in cleaned:
        return cleaned.replace(".", "").replace(",", ".")

    if "." in cleaned:
        whole, _, fraction = cleaned.rpartition(".")
        if len(fraction) == 3 and whole.replace(".", "").isdigit():
            return cleaned.replace(".", "")
        return cleaned

    return cleaned


def _normalize_for_search(text: str) -> str:
    folded = unicodedata.normalize("NFKD", text)
    ascii_text = "".join(char for char in folded if not unicodedata.combining(char))
    return ascii_text.lower()


def _first_text(node: Mapping[str, Any], *keys: str) -> str:
    for key in keys:
        value = _optional_text(node.get(key))
        if value:
            return value
    return ""


def _optional_text(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
