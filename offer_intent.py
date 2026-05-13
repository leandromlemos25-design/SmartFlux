from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)
class ProductIntent:
    key: str
    label: str
    request_patterns: tuple[str, ...]
    main_title_patterns: tuple[str, ...]
    accessory_patterns: tuple[str, ...]
    default_search_terms: tuple[str, str, str]
    min_price: Decimal
    unsafe_reason: str


PHONE_ACCESSORIES = (
    r"\bcapa\b",
    r"\bcapinha\b",
    r"\bcase\b",
    r"\bpelicula\b",
    r"\bvidro\b",
    r"\bcarregador\b",
    r"\bcabo\b",
    r"\bsuporte\b",
    r"\bdock\b",
    r"\blente\b",
)

COMPUTER_ACCESSORIES = (
    r"\bcooler\b",
    r"\bfan\b",
    r"\bmouse\b",
    r"\bmousepad\b",
    r"\bteclado\b",
    r"\bmonitor\b",
    r"\bheadset\b",
    r"\bwebcam\b",
    r"\bgabinete\b",
    r"\bplaca\s+mae\b",
    r"\bplaca\s+de\s+video\b",
    r"\bmemoria\s+ram\b",
    r"\bssd\b",
    r"\bfonte\b",
    r"\bcabo\b",
    r"\badaptador\b",
    r"\bsuporte\b",
)

PRODUCT_INTENTS: tuple[ProductIntent, ...] = (
    ProductIntent(
        key="iphone",
        label="iPhone",
        request_patterns=(r"\biphone\b",),
        main_title_patterns=(r"\biphone\b", r"\bsmartphone\s+apple\b", r"\bcelular\s+apple\b"),
        accessory_patterns=PHONE_ACCESSORIES,
        default_search_terms=("Smartphone Apple iPhone Original Lacrado", "iPhone Original Lacrado", "iPhone"),
        min_price=Decimal("1000.00"),
        unsafe_reason="Apple caro demais para esse preco",
    ),
    ProductIntent(
        key="smartphone",
        label="smartphone",
        request_patterns=(
            r"\bcelular\b",
            r"\bsmartphone\b",
            r"\bgalaxy\b",
            r"\bsamsung\b",
            r"\bxiaomi\b",
            r"\bredmi\b",
            r"\bpoco\b",
            r"\bmotorola\b",
            r"\bmoto\s*g\b",
        ),
        main_title_patterns=(
            r"\bcelular\b",
            r"\bsmartphone\b",
            r"\bgalaxy\b",
            r"\bsamsung\b",
            r"\bxiaomi\b",
            r"\bredmi\b",
            r"\bpoco\b",
            r"\bmotorola\b",
            r"\bmoto\s*g\b",
        ),
        accessory_patterns=PHONE_ACCESSORIES,
        default_search_terms=("Smartphone Android 5G 256GB Original", "Celular Android 5G Original", "Smartphone 5G"),
        min_price=Decimal("250.00"),
        unsafe_reason="celular caro demais para esse preco",
    ),
    ProductIntent(
        key="notebook",
        label="notebook",
        request_patterns=(r"\bnotebook\b", r"\blaptop\b", r"\bultrabook\b"),
        main_title_patterns=(r"\bnotebook\b", r"\blaptop\b", r"\bultrabook\b", r"\bmacbook\b"),
        accessory_patterns=COMPUTER_ACCESSORIES,
        default_search_terms=("Notebook Core i5 8GB SSD Original", "Notebook Core i5 SSD", "Notebook Core i5"),
        min_price=Decimal("800.00"),
        unsafe_reason="computador caro demais para esse preco",
    ),
    ProductIntent(
        key="computer",
        label="computador completo",
        request_patterns=(r"\bcomputador\b", r"\bdesktop\b", r"\bpc\s+gamer\b", r"\bpc\s+completo\b", r"\bpc\b"),
        main_title_patterns=(
            r"\bcomputador\b",
            r"\bdesktop\b",
            r"\bmini\s*pc\b",
            r"\ball\s*in\s*one\b",
            r"\bpc\s+(?:gamer\s+)?completo\b",
            r"\bcpu\s+gamer\b",
        ),
        accessory_patterns=COMPUTER_ACCESSORIES,
        default_search_terms=("Computador Completo Intel Core i5 8GB SSD", "Desktop Completo Core i5 SSD", "Computador Completo"),
        min_price=Decimal("800.00"),
        unsafe_reason="computador caro demais para esse preco",
    ),
    ProductIntent(
        key="monitor",
        label="monitor",
        request_patterns=(r"\bmonitor\b",),
        main_title_patterns=(r"\bmonitor\b",),
        accessory_patterns=(r"\bsuporte\b", r"\bcabo\b", r"\badaptador\b", r"\bbase\b", r"\bbraco\b"),
        default_search_terms=("Monitor Gamer 24 Polegadas Full HD HDMI", "Monitor 24 Full HD HDMI", "Monitor Gamer"),
        min_price=Decimal("200.00"),
        unsafe_reason="monitor caro demais para esse preco",
    ),
    ProductIntent(
        key="tv",
        label="TV",
        request_patterns=(r"\bsmart\s*tv\b", r"\btelevisao\b", r"\btv\b"),
        main_title_patterns=(r"\bsmart\s*tv\b", r"\btelevisao\b", r"\btv\s+\d{2}\b", r"\b\d{2}\s*(?:pol|polegadas)\b"),
        accessory_patterns=(r"\bcontrole\s+remoto\b", r"\bsuporte\b", r"\bcabo\b", r"\bantena\b", r"\bconversor\b", r"\bbase\b"),
        default_search_terms=("Smart TV 55 Polegadas 4K UHD", "Smart TV 55 4K", "Smart TV 55"),
        min_price=Decimal("450.00"),
        unsafe_reason="TV cara demais para esse preco",
    ),
    ProductIntent(
        key="console",
        label="console",
        request_patterns=(r"\bps5\b", r"\bplaystation\b", r"\bxbox\b", r"\bnintendo\b", r"\bswitch\b"),
        main_title_patterns=(r"\bconsole\b", r"\bps5\b", r"\bplaystation\b", r"\bxbox\b", r"\bnintendo\s+switch\b", r"\bswitch\s*2?\b"),
        accessory_patterns=(r"\bcontrole\b", r"\bjoystick\b", r"\bcarregador\b", r"\bsuporte\b", r"\bcapa\b", r"\bcase\b", r"\bjogo\b", r"\bmidia\b"),
        default_search_terms=("Console PlayStation 5 Original Sony", "PlayStation 5 Console Original", "PS5 Console"),
        min_price=Decimal("900.00"),
        unsafe_reason="console caro demais para esse preco",
    ),
    ProductIntent(
        key="air_conditioner",
        label="ar condicionado",
        request_patterns=(r"\bar\s+condicionado\b", r"\bcondicionado\b", r"\bsplit\b", r"\binverter\b", r"\bbtus?\b"),
        main_title_patterns=(r"\bar\s+condicionado\b", r"\bsplit\b", r"\binverter\b", r"\bjanela\b.*\b(?:frio|quente)\b"),
        accessory_patterns=(r"\bcontrole\b", r"\bplaca\b", r"\bsensor\b", r"\bcapacitor\b", r"\bfiltro\b", r"\bsuporte\b", r"\bdreno\b"),
        default_search_terms=("Ar Condicionado Split Inverter 12000 BTUs", "Ar Condicionado Split 12000 BTUs", "Ar Condicionado"),
        min_price=Decimal("700.00"),
        unsafe_reason="ar condicionado caro demais para esse preco",
    ),
    ProductIntent(
        key="appliance",
        label="eletrodomestico",
        request_patterns=(r"\bgeladeira\b", r"\brefrigerador\b", r"\bfreezer\b", r"\bfogao\b", r"\blava\s+e\s+seca\b", r"\blavadora\b"),
        main_title_patterns=(r"\bgeladeira\b", r"\brefrigerador\b", r"\bfreezer\b", r"\bfogao\b", r"\blava\s+e\s+seca\b", r"\blavadora\b"),
        accessory_patterns=(r"\bfiltro\b", r"\bpeca\b", r"\bpecas\b", r"\bprateleira\b", r"\bgaveta\b", r"\bborracha\b", r"\bresistencia\b", r"\bbotao\b"),
        default_search_terms=("Geladeira Frost Free 375 Litros Inox", "Geladeira Frost Free", "Geladeira"),
        min_price=Decimal("250.00"),
        unsafe_reason="eletrodomestico caro demais para esse preco",
    ),
    ProductIntent(
        key="smartwatch",
        label="smartwatch",
        request_patterns=(r"\bsmartwatch\b", r"\bsmart\s*watch\b", r"\bapple\s+watch\b", r"\bgalaxy\s+watch\b", r"\brelogio\b"),
        main_title_patterns=(r"\bsmartwatch\b", r"\bsmart\s*watch\b", r"\bapple\s+watch\b", r"\bgalaxy\s+watch\b", r"\bsmart\s*band\b", r"\bmi\s*band\b"),
        accessory_patterns=(r"\bpulseira\b", r"\bbracelete\b", r"\bpelicula\b", r"\bcarregador\b", r"\bcapa\b", r"\bcase\b"),
        default_search_terms=("Smartwatch Original Bluetooth", "Smartwatch Original", "Smartwatch"),
        min_price=Decimal("60.00"),
        unsafe_reason="smartwatch caro demais para esse preco",
    ),
    ProductIntent(
        key="headphone",
        label="fone de ouvido",
        request_patterns=(r"\bfone\b", r"\bheadphone\b", r"\bairpods\b", r"\bgalaxy\s+buds\b", r"\bearbuds\b"),
        main_title_patterns=(r"\bfone\b", r"\bheadphone\b", r"\bearbuds\b", r"\bairpods\b", r"\bgalaxy\s+buds\b", r"\bjbl\s+tune\b"),
        accessory_patterns=(r"\bcapa\b", r"\bcase\b", r"\bestojo\b", r"\bborracha\b", r"\bespuma\b", r"\bcabo\b", r"\bcarregador\b"),
        default_search_terms=("Fone Bluetooth Original JBL", "Fone Bluetooth Original", "Fone Bluetooth"),
        min_price=Decimal("20.00"),
        unsafe_reason="fone caro demais para esse preco",
    ),
    ProductIntent(
        key="perfume",
        label="perfume",
        request_patterns=(r"\bperfume\b", r"\bcolonia\b", r"\b212\s+vip\b"),
        main_title_patterns=(r"\bperfume\b", r"\bcolonia\b", r"\beau\s+de\b", r"\bedp\b", r"\bedt\b", r"\bparfum\b"),
        accessory_patterns=(r"\bamostra\b", r"\bdecant\b", r"\bfrasco\s+vazio\b", r"\bcontratipo\b", r"\binspirado\b", r"\bsimilar\b"),
        default_search_terms=("Perfume Importado Original 100ml", "Perfume Original Importado", "Perfume Original"),
        min_price=Decimal("30.00"),
        unsafe_reason="perfume caro demais para esse preco",
    ),
)

BAD_OFFER_PATTERNS = (
    r"\b1\s+linha\b",
    r"\bprimeira\s+linha\b",
    r"\breplica\b",
    r"\bsemi\s+novo\b",
    r"\bseminovo\b",
    r"\busado\b",
)

ACCESSORY_REQUEST_PREFIX_RE = re.compile(
    r"^\s*(?:quero|procura(?:r)?|busca(?:r)?|acha(?:r)?|manda|me\s+ve|tem|preciso\s+de)?\s*"
    r"(?:um|uma|o|a|uns|umas)?\s*"
    r"(capa|capinha|case|pelicula|vidro|carregador|cabo|suporte|controle|joystick|cooler|fan|mouse|teclado|mousepad|webcam|pulseira|bracelete|peca|pecas|filtro|amostra|decant)\b"
)

GENERIC_ACCESSORY_PATTERNS = (
    r"\badaptador\b",
    r"\badesivo\b",
    r"\bamostra\b",
    r"\bbateria\b",
    r"\bbase\b",
    r"\bbolsa\b",
    r"\bborracha\b",
    r"\bbotao\b",
    r"\bbroca\b",
    r"\bcabo\b",
    r"\bcapa\b",
    r"\bcapinha\b",
    r"\bcarregador\b",
    r"\bcase\b",
    r"\bchaveiro\b",
    r"\bcontrole\b",
    r"\bfiltro\b",
    r"\bkit\s+(?:de\s+)?(?:pecas|reposicao|acessorios)\b",
    r"\blamina\b",
    r"\blente\b",
    r"\bpeca\b",
    r"\bpecas\b",
    r"\bpelicula\b",
    r"\brefil\b",
    r"\breparo\b",
    r"\breposicao\b",
    r"\brodinha\b",
    r"\bsuporte\b",
    r"\btampa\b",
    r"\bvidro\b",
)

STOPWORDS = {
    "a",
    "agora",
    "algum",
    "alguma",
    "as",
    "ate",
    "barata",
    "barato",
    "boa",
    "bom",
    "buscar",
    "com",
    "compra",
    "comprar",
    "da",
    "das",
    "de",
    "desconto",
    "do",
    "dos",
    "em",
    "encontra",
    "encontrar",
    "eu",
    "favor",
    "legal",
    "manda",
    "me",
    "melhor",
    "no",
    "na",
    "o",
    "oferta",
    "ofertas",
    "os",
    "para",
    "por",
    "pra",
    "preciso",
    "procura",
    "procurar",
    "promocao",
    "quero",
    "um",
    "uma",
    "uns",
    "ver",
    "ve",
    "voce",
}


def normalize_text(text: str) -> str:
    folded = unicodedata.normalize("NFKD", text or "")
    ascii_text = "".join(char for char in folded if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", ascii_text.lower()).strip()


def detect_product_intent(user_request: str) -> Optional[ProductIntent]:
    normalized = normalize_text(user_request)
    if not normalized or _is_explicit_accessory_request(normalized):
        return None

    candidates: list[tuple[int, int, ProductIntent]] = []
    for index, intent in enumerate(PRODUCT_INTENTS):
        first_match = _first_match(normalized, intent.request_patterns)
        if first_match:
            candidates.append((first_match.start(), index, intent))

    if not candidates:
        return None

    return min(candidates, key=lambda item: (item[0], item[1]))[2]


def default_search_terms_for_request(user_request: str) -> Optional[tuple[str, str, str]]:
    intent = detect_product_intent(user_request)
    return intent.default_search_terms if intent else None


def title_validation_error(title: str, intent: ProductIntent) -> Optional[str]:
    normalized_title = normalize_text(title)
    if not normalized_title:
        return "resultado sem titulo."

    bad_match = _first_match(normalized_title, BAD_OFFER_PATTERNS)
    if bad_match:
        return f"resultado contem termo inseguro ({bad_match})."

    main_match = _first_match(normalized_title, intent.main_title_patterns)
    accessory_match = _first_match(normalized_title, intent.accessory_patterns)

    if accessory_match and (not main_match or _match_starts_before(accessory_match, main_match)):
        return f"resultado parece acessorio/periferico de {intent.label} ({accessory_match.group(0)}), nao produto principal."

    if not main_match:
        return f"resultado nao parece {intent.label}."

    return None


def generic_title_validation_error(user_request: str, candidate_title: str) -> Optional[str]:
    normalized_request = normalize_text(user_request)
    if not normalized_request or _is_explicit_accessory_request(normalized_request):
        return None

    request_terms = _core_terms(normalized_request)
    if not request_terms:
        return None

    normalized_title = normalize_text(candidate_title)
    if not normalized_title:
        return "resultado sem titulo."

    bad_match = _first_match(normalized_title, BAD_OFFER_PATTERNS)
    if bad_match:
        return f"resultado contem termo inseguro ({bad_match.group(0)})."

    accessory_match = _first_match(normalized_title, GENERIC_ACCESSORY_PATTERNS)
    if accessory_match and _looks_like_accessory_for_request(normalized_title, request_terms, accessory_match):
        return f"resultado parece acessorio/peca ({accessory_match.group(0)}), nao o produto pedido."

    matched_terms = _matched_terms(request_terms, normalized_title)
    if not matched_terms:
        return "resultado nao tem aderencia suficiente com o pedido."

    primary_term = request_terms[0]
    if (
        len(request_terms) >= 2
        and primary_term not in matched_terms
        and not _has_strong_secondary_match(request_terms, matched_terms)
    ):
        return f"resultado nao confirma o produto principal ({primary_term})."

    return None


def min_price_for_request(user_request: str) -> Optional[Decimal]:
    intent = detect_product_intent(user_request)
    return intent.min_price if intent else None


def _core_terms(normalized_text: str) -> list[str]:
    words = re.findall(r"[a-z0-9]+", normalized_text)
    terms: list[str] = []
    for word in words:
        if len(word) <= 1 or word in STOPWORDS:
            continue
        if word not in terms:
            terms.append(word)
    return terms[:8]


def _matched_terms(request_terms: list[str], normalized_title: str) -> set[str]:
    matches: set[str] = set()
    for term in request_terms:
        if re.search(rf"(?<!\w){re.escape(term)}(?!\w)", normalized_title):
            matches.add(term)
    return matches


def _has_strong_secondary_match(request_terms: list[str], matched_terms: set[str]) -> bool:
    if len(matched_terms) >= 2:
        return True
    return any(term in matched_terms and (term.isdigit() or len(term) >= 5) for term in request_terms[1:])


def _looks_like_accessory_for_request(
    normalized_title: str,
    request_terms: list[str],
    accessory_match: re.Match[str],
) -> bool:
    first_product_pos = _first_term_position(normalized_title, request_terms)
    if first_product_pos is None:
        return True
    if accessory_match.start() < first_product_pos:
        return True

    after_accessory = normalized_title[accessory_match.end():]
    return bool(
        re.search(r"\b(?:para|pra|p|compativel|compatibilidade|de|do|da)\b", after_accessory)
        and any(re.search(rf"(?<!\w){re.escape(term)}(?!\w)", after_accessory) for term in request_terms)
    )


def _first_term_position(normalized_title: str, request_terms: list[str]) -> Optional[int]:
    positions: list[int] = []
    for term in request_terms:
        match = re.search(rf"(?<!\w){re.escape(term)}(?!\w)", normalized_title)
        if match:
            positions.append(match.start())
    return min(positions) if positions else None


def _is_explicit_accessory_request(normalized_request: str) -> bool:
    if re.search(r"\b(computador|desktop|pc)\b.*\bcompleto\b", normalized_request):
        return False
    if ACCESSORY_REQUEST_PREFIX_RE.search(normalized_request):
        return True
    return bool(
        re.search(
            r"\b(capa|capinha|case|pelicula|carregador|cooler|mouse|teclado|controle|pulseira|filtro|amostra)\s+(?:para|de|do|da)\b",
            normalized_request,
        )
    )


def _matches_any(text: str, patterns: tuple[str, ...]) -> bool:
    return any(re.search(pattern, text) for pattern in patterns)


def _first_match(text: str, patterns: tuple[str, ...]) -> Optional[re.Match[str]]:
    matches = [match for pattern in patterns for match in [re.search(pattern, text)] if match]
    if not matches:
        return None
    return min(matches, key=lambda match: match.start())


def _match_starts_before(left: re.Match[str], right: re.Match[str]) -> bool:
    return left.start() <= right.start()
