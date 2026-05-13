from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Iterable, Optional

from offer_intent import default_search_terms_for_request, detect_product_intent, generic_title_validation_error, title_validation_error


TAG_ORDER = ("BUSCAR", "BUSCAR_ALT", "BUSCAR_SIMPLES")
TAG_RE = re.compile(r"^\[(BUSCAR|BUSCAR_ALT|BUSCAR_SIMPLES):\s*(.+?)\]$")

ACCESSORY_WORDS = {
    "adaptador",
    "cabo",
    "capa",
    "capinha",
    "carregador",
    "case",
    "controle remoto",
    "dock",
    "lente",
    "pelicula",
    "peca",
    "pecas",
    "pulseira",
    "suporte",
    "tela",
    "vidro",
}

USED_OR_FAKE_WORDS = {
    "1 linha",
    "primeira linha",
    "replica",
    "semi novo",
    "seminovo",
    "usado",
}

PRODUCT_WORDS = {
    "airpods",
    "apple watch",
    "ar condicionado",
    "celular",
    "console",
    "computador",
    "desktop",
    "fone",
    "galaxy",
    "geladeira",
    "iphone",
    "monitor",
    "moto",
    "notebook",
    "pc",
    "pc gamer",
    "perfume",
    "playstation",
    "ps5",
    "redmi",
    "smart tv",
    "smartphone",
    "smartwatch",
    "switch",
    "tv",
    "xbox",
}

REDIRECT_MODELS = {
    "iphone 17 plus": "iPhone Air",
    "iphone 18": "iPhone 17 Pro Max",
    "galaxy s27": "Galaxy S26 Ultra",
}


@dataclass(frozen=True)
class SearchTags:
    buscar: str
    buscar_alt: str
    buscar_simples: str

    def as_lines(self) -> str:
        return "\n".join(
            (
                f"[BUSCAR: {self.buscar}]",
                f"[BUSCAR_ALT: {self.buscar_alt}]",
                f"[BUSCAR_SIMPLES: {self.buscar_simples}]",
            )
        )


@dataclass(frozen=True)
class TetecoValidationResult:
    ok: bool
    response: str
    tags: Optional[SearchTags]
    errors: tuple[str, ...]
    warnings: tuple[str, ...] = ()


def validate_teteco_response(user_request: str, ai_response: str) -> TetecoValidationResult:
    """Validate the Teteco AI contract before sending the response to the user."""
    errors: list[str] = []
    warnings: list[str] = []

    lines = _meaningful_lines(ai_response)
    if len(lines) < 3:
        return TetecoValidationResult(False, ai_response, None, ("Resposta curta demais; faltam tags.",))

    tag_lines = lines[-3:]
    parsed: dict[str, str] = {}

    for expected, line in zip(TAG_ORDER, tag_lines):
        match = TAG_RE.match(line)
        if not match:
            errors.append(f"Linha final invalida para {expected}: {line!r}.")
            continue
        tag_name, term = match.groups()
        if tag_name != expected:
            errors.append(f"Tag fora de ordem: esperado {expected}, veio {tag_name}.")
        parsed[tag_name] = _clean_term(term)

    all_tag_lines = [line for line in lines if TAG_RE.match(line)]
    if len(all_tag_lines) != 3:
        errors.append(f"A resposta deve conter exatamente 3 tags; contem {len(all_tag_lines)}.")

    if set(parsed) == set(TAG_ORDER):
        tags = SearchTags(
            buscar=parsed["BUSCAR"],
            buscar_alt=parsed["BUSCAR_ALT"],
            buscar_simples=parsed["BUSCAR_SIMPLES"],
        )
        errors.extend(_validate_terms(user_request, tags))
        warnings.extend(_model_warnings(user_request, tags))
    else:
        tags = None

    return TetecoValidationResult(not errors, ai_response, tags, tuple(errors), tuple(warnings))


def require_valid_teteco_response(user_request: str, ai_response: str) -> SearchTags:
    result = validate_teteco_response(user_request, ai_response)
    if not result.ok or result.tags is None:
        raise ValueError("Resposta Teteco invalida: " + " | ".join(result.errors))
    return result.tags


def repair_teteco_response(user_request: str, ai_response: str) -> str:
    """Return a safe response. Valid AI output is preserved; invalid output gets fallback tags."""
    result = validate_teteco_response(user_request, ai_response)
    if result.ok:
        return ai_response.strip()

    intro = _strip_existing_tags(ai_response).strip()
    intro = _safe_intro(user_request, intro)
    tags = build_fallback_tags(user_request)
    return f"{intro}\n{tags.as_lines()}"


def build_fallback_tags(user_request: str) -> SearchTags:
    """Deterministic fallback when the AI misses the required contract."""
    request = _normalize(user_request)

    for bad_model, replacement in REDIRECT_MODELS.items():
        if bad_model in request:
            return _tags_for_model(replacement)

    if "iphone 17 pro max" in request:
        return _tags_for_model("iPhone 17 Pro Max")
    if "iphone 17 pro" in request:
        return _tags_for_model("iPhone 17 Pro")
    if "iphone 17e" in request:
        return _tags_for_model("iPhone 17e")
    if "iphone 17" in request:
        return _tags_for_model("iPhone 17")
    if "iphone 16" in request:
        return _tags_for_model("iPhone 16")
    if "iphone" in request:
        return _tags_for_model("iPhone 17")

    if "s26 ultra" in request or "galaxy s26 ultra" in request:
        return _tags_for_model("Samsung Galaxy S26 Ultra")
    if "s26+" in request or "s26 plus" in request:
        return _tags_for_model("Samsung Galaxy S26+")
    if "s26" in request:
        return _tags_for_model("Samsung Galaxy S26")
    if "s25 edge" in request:
        return _tags_for_model("Samsung Galaxy S25 Edge")
    if "s25 ultra" in request:
        return _tags_for_model("Samsung Galaxy S25 Ultra")
    if "s25" in request:
        return _tags_for_model("Samsung Galaxy S25")

    if "samsung" in request and any(word in request for word in ("barato", "custo beneficio", "entrada")):
        return _tags_for_model("Samsung Galaxy A56 5G")
    if "galaxy a56" in request or "a56" in request:
        return _tags_for_model("Samsung Galaxy A56 5G")
    if "galaxy a36" in request or "a36" in request:
        return _tags_for_model("Samsung Galaxy A36 5G")
    if "galaxy a16" in request or "a16" in request:
        return _tags_for_model("Samsung Galaxy A16 5G")
    if "samsung" in request or "galaxy" in request:
        return _tags_for_model("Samsung Galaxy S26")

    if "redmi" in request:
        return _tags_for_model("Xiaomi Redmi Note 14")
    if "poco f7" in request:
        return _tags_for_model("Xiaomi Poco F7")
    if "poco" in request:
        return _tags_for_model("Xiaomi Poco X7")
    if "xiaomi" in request:
        return _tags_for_model("Xiaomi Redmi Note 14")

    if "moto g" in request or "motorola" in request:
        return _tags_for_model("Motorola Moto G85")

    if "notebook dell" in request or ("notebook" in request and "dell" in request):
        return SearchTags("Notebook Dell Inspiron 15 Core i5 8GB SSD", "Notebook Dell Inspiron i5", "Notebook Dell")
    if "notebook samsung" in request:
        return SearchTags("Notebook Samsung Galaxy Book Core i5 8GB SSD", "Notebook Samsung Galaxy Book", "Notebook Samsung")
    if "notebook lenovo" in request:
        return SearchTags("Notebook Lenovo IdeaPad Core i5 8GB SSD", "Notebook Lenovo IdeaPad i5", "Notebook Lenovo")
    if "notebook acer" in request:
        return SearchTags("Notebook Acer Aspire Core i5 8GB SSD", "Notebook Acer Aspire i5", "Notebook Acer")
    if "notebook asus" in request:
        return SearchTags("Notebook ASUS VivoBook Core i5 8GB SSD", "Notebook ASUS VivoBook i5", "Notebook ASUS")
    if "notebook" in request or "laptop" in request:
        return SearchTags("Notebook Dell Inspiron 15 Core i5 8GB SSD", "Notebook Dell Inspiron i5", "Notebook Dell")

    if "pc gamer" in request or ("computador" in request and "gamer" in request):
        return SearchTags(
            "PC Gamer Completo Ryzen 5 16GB SSD Placa de Video",
            "Computador Gamer Completo Ryzen 5",
            "PC Gamer Completo",
        )

    if "tv lg" in request or ("tv" in request and "lg" in request):
        return SearchTags("Smart TV LG 55 Polegadas 4K UHD", "Smart TV LG 4K 55", "Smart TV LG")
    if "tv samsung" in request:
        return SearchTags("Smart TV Samsung QLED 55 Polegadas 4K", "Smart TV Samsung QLED 55", "Smart TV Samsung")
    if "tv tcl" in request:
        return SearchTags("Smart TV TCL QLED 55 Polegadas 4K", "Smart TV TCL QLED 55", "Smart TV TCL")
    if "tv" in request:
        return SearchTags("Smart TV 55 Polegadas 4K UHD", "Smart TV 55 4K", "Smart TV 55")

    if "ps5" in request or "playstation" in request:
        return SearchTags("Console PlayStation 5 Original Sony", "PlayStation 5 Console Original", "PS5 Console")
    if "xbox" in request:
        return SearchTags("Console Xbox Series S Original Microsoft", "Xbox Series S Original", "Xbox Series S")
    if "switch" in request or "nintendo" in request:
        return SearchTags("Console Nintendo Switch 2 Original", "Nintendo Switch 2 Original", "Switch 2")

    if "airpods" in request:
        return SearchTags("Fone de Ouvido Apple AirPods Pro 2 Original", "AirPods Pro 2 Original Apple", "AirPods Pro")
    if "galaxy buds" in request:
        return SearchTags("Fone Samsung Galaxy Buds 3 Pro Original", "Galaxy Buds 3 Pro Original", "Galaxy Buds")
    if "fone" in request or "headphone" in request:
        return SearchTags("Fone JBL Tune 770NC Bluetooth Original", "JBL Tune 770NC Original", "JBL Tune 770NC")

    if "apple watch" in request:
        return SearchTags("Smartwatch Apple Watch Series 11 Original GPS", "Apple Watch Series 11 Original", "Apple Watch")
    if "galaxy watch" in request:
        return SearchTags("Smartwatch Samsung Galaxy Watch 8 Original", "Galaxy Watch 8 Original", "Galaxy Watch 8")
    if "relogio" in request or "smartwatch" in request:
        return SearchTags("Smartwatch Xiaomi Smart Band 9 Original", "Xiaomi Smart Band 9 Original", "Smart Band 9")

    if "212 vip" in request:
        return SearchTags("Perfume Carolina Herrera 212 VIP Original 100ml EDP", "Perfume 212 VIP Original 100ml", "212 VIP perfume")
    if "perfume" in request:
        return SearchTags("Perfume Importado Original 100ml", "Perfume Original Importado", "Perfume original")

    if "geladeira brastemp" in request:
        return SearchTags("Geladeira Brastemp Frost Free 375 Litros Inox", "Geladeira Brastemp Frost Free", "Geladeira Brastemp")
    if "geladeira" in request:
        return SearchTags("Geladeira Frost Free 375 Litros Inox", "Geladeira Frost Free", "Geladeira")

    catalog_terms = default_search_terms_for_request(user_request)
    if catalog_terms:
        return SearchTags(*catalog_terms)

    return _generic_tags(user_request)


def _validate_terms(user_request: str, tags: SearchTags) -> list[str]:
    errors: list[str] = []
    request = _normalize(user_request)
    terms = (tags.buscar, tags.buscar_alt, tags.buscar_simples)
    normalized_terms = [_normalize(term) for term in terms]

    for tag_name, term in zip(TAG_ORDER, terms):
        if not term:
            errors.append(f"{tag_name} esta vazio.")
        if len(term) > 120:
            errors.append(f"{tag_name} esta grande demais.")
        if "\n" in term or "[" in term or "]" in term:
            errors.append(f"{tag_name} contem caracteres invalidos.")

    simple_words = _words(tags.buscar_simples)
    if not 2 <= len(simple_words) <= 4:
        errors.append("BUSCAR_SIMPLES deve ter de 2 a 4 palavras.")

    request_intent = detect_product_intent(user_request)
    if request_intent:
        for tag_name, term in zip(TAG_ORDER, terms):
            relevance_error = title_validation_error(term, request_intent)
            if relevance_error:
                errors.append(f"{tag_name} {relevance_error}")
    else:
        for tag_name, term in zip(TAG_ORDER, terms):
            relevance_error = generic_title_validation_error(user_request, term)
            if relevance_error:
                errors.append(f"{tag_name} {relevance_error}")

    for tag_name, normalized in zip(TAG_ORDER, normalized_terms):
        fake_word = _contains_any(normalized, USED_OR_FAKE_WORDS)
        if fake_word:
            errors.append(f"{tag_name} contem termo inseguro: {fake_word}.")

    if "s26" in request and any("s25" in term for term in normalized_terms):
        errors.append("Pedido de Galaxy S26 foi rebaixado para S25.")

    if "iphone 17" in request and not any("iphone 17" in term or "iphone air" in term for term in normalized_terms):
        errors.append("Pedido de iPhone 17 nao gerou busca para linha iPhone 17.")

    if "iphone 17 plus" in request and any("iphone 17 plus" in term for term in normalized_terms):
        errors.append("iPhone 17 Plus deve ser redirecionado para iPhone Air ou iPhone 17 Pro Max.")

    return errors


def _model_warnings(user_request: str, tags: SearchTags) -> list[str]:
    warnings: list[str] = []
    request = _normalize(user_request)
    normalized = " | ".join(_normalize(term) for term in (tags.buscar, tags.buscar_alt, tags.buscar_simples))

    for bad_model, replacement in REDIRECT_MODELS.items():
        if bad_model in request and _normalize(replacement) not in normalized:
            warnings.append(f"Modelo {bad_model} deveria redirecionar para {replacement}.")

    return warnings


def _tags_for_model(model: str) -> SearchTags:
    normalized = _normalize(model)

    if normalized.startswith("iphone") or normalized.startswith("apple iphone"):
        short = model.replace("Apple ", "")
        storage = "256GB"
        return SearchTags(
            f"Smartphone Apple {short} {storage} Original Lacrado",
            f"{short} Original Lacrado",
            short,
        )

    if normalized.startswith("samsung galaxy"):
        short = model.replace("Samsung ", "")
        storage = "256GB"
        return SearchTags(
            f"Smartphone Samsung {short} {storage} Original Lacrado",
            f"Samsung {short} Original",
            short,
        )

    if normalized.startswith("xiaomi"):
        short = model.replace("Xiaomi ", "")
        return SearchTags(
            f"Smartphone {model} 256GB Original Lacrado",
            f"{model} Original",
            short,
        )

    if normalized.startswith("motorola"):
        short = model.replace("Motorola ", "")
        return SearchTags(
            f"Smartphone {model} 256GB Original Lacrado",
            f"{model} Original",
            short,
        )

    return _generic_tags(model)


def _generic_tags(user_request: str) -> SearchTags:
    cleaned = _clean_term(user_request)
    if not cleaned:
        cleaned = "produto oferta"
    words = _words(cleaned)
    simple = " ".join(words[:4]) if len(words) >= 2 else cleaned
    return SearchTags(
        f"{cleaned} Original",
        cleaned,
        simple,
    )


def _safe_intro(user_request: str, intro: str) -> str:
    intro = re.sub(r"\s+", " ", intro).strip()
    if not intro or len(intro) > 220:
        return "Boa! Vou buscar opcoes reais e evitar resultados ruins ou acessorios indesejados."
    if any(word in _normalize(intro) for word in ("r$ ", "por apenas", "estoque", "cupom garantido")):
        return "Boa! Vou buscar opcoes reais e evitar resultados ruins ou acessorios indesejados."
    if _contains_any(_normalize(user_request), PRODUCT_WORDS) and _contains_any(_normalize(intro), ACCESSORY_WORDS):
        return "Boa! Vou focar no produto principal e evitar acessorios indesejados."
    return intro


def _strip_existing_tags(text: str) -> str:
    return "\n".join(line for line in text.splitlines() if not TAG_RE.match(line.strip()))


def _meaningful_lines(text: str) -> list[str]:
    return [line.strip() for line in text.strip().splitlines() if line.strip()]


def _clean_term(value: str) -> str:
    value = re.sub(r"\s+", " ", value).strip()
    value = value.strip(" .;:-")
    return value[:140]


def _normalize(text: str) -> str:
    folded = unicodedata.normalize("NFKD", text)
    ascii_text = "".join(char for char in folded if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", ascii_text.lower()).strip()


def _words(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z0-9+]+", _normalize(text))


def _contains_any(text: str, words: Iterable[str]) -> Optional[str]:
    for word in words:
        normalized_word = _normalize(word)
        if re.search(rf"(?<!\w){re.escape(normalized_word)}(?!\w)", text):
            return word
    return None


def _is_main_product_request(normalized_request: str) -> bool:
    if _contains_any(normalized_request, ACCESSORY_WORDS):
        return False
    return _contains_any(normalized_request, PRODUCT_WORDS) is not None
