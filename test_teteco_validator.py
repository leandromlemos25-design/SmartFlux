from __future__ import annotations

import unittest

from teteco_validator import (
    SearchTags,
    build_fallback_tags,
    repair_teteco_response,
    require_valid_teteco_response,
    validate_teteco_response,
)


class TetecoValidatorTest(unittest.TestCase):
    def test_accepts_valid_response(self) -> None:
        response = "\n".join(
            (
                "Boa escolha! Vou focar em aparelho original.",
                "[BUSCAR: Smartphone Apple iPhone 17 256GB Original Lacrado]",
                "[BUSCAR_ALT: iPhone 17 Original Lacrado]",
                "[BUSCAR_SIMPLES: iPhone 17]",
            )
        )
        result = validate_teteco_response("quero iphone 17", response)
        self.assertTrue(result.ok, result.errors)
        self.assertEqual(result.tags, SearchTags("Smartphone Apple iPhone 17 256GB Original Lacrado", "iPhone 17 Original Lacrado", "iPhone 17"))

    def test_rejects_missing_tags(self) -> None:
        result = validate_teteco_response("quero ps5", "Vou procurar pra voce.")
        self.assertFalse(result.ok)

    def test_rejects_text_after_tags(self) -> None:
        response = "\n".join(
            (
                "Boa!",
                "[BUSCAR: Console PlayStation 5 Original Sony]",
                "[BUSCAR_ALT: PlayStation 5 Console Original]",
                "[BUSCAR_SIMPLES: PS5 Console]",
                "Achei!",
            )
        )
        result = validate_teteco_response("ps5", response)
        self.assertFalse(result.ok)

    def test_rejects_accessory_when_user_wants_main_product(self) -> None:
        response = "\n".join(
            (
                "Boa!",
                "[BUSCAR: Capa iPhone 17 Original]",
                "[BUSCAR_ALT: Capinha iPhone 17]",
                "[BUSCAR_SIMPLES: Capa iPhone]",
            )
        )
        result = validate_teteco_response("iphone 17", response)
        self.assertFalse(result.ok)
        self.assertIn("acessorio", " ".join(result.errors))

    def test_allows_accessory_when_user_asks_accessory(self) -> None:
        response = "\n".join(
            (
                "Boa!",
                "[BUSCAR: Capa iPhone 17 Silicone Original]",
                "[BUSCAR_ALT: Capinha iPhone 17]",
                "[BUSCAR_SIMPLES: Capa iPhone]",
            )
        )
        result = validate_teteco_response("quero capa iphone 17", response)
        self.assertTrue(result.ok, result.errors)

    def test_rejects_s26_downgrade_to_s25(self) -> None:
        response = "\n".join(
            (
                "Boa!",
                "[BUSCAR: Smartphone Samsung Galaxy S25 Ultra 256GB Original]",
                "[BUSCAR_ALT: Samsung Galaxy S25 Ultra Original]",
                "[BUSCAR_SIMPLES: Galaxy S25]",
            )
        )
        result = validate_teteco_response("galaxy s26", response)
        self.assertFalse(result.ok)

    def test_fallback_for_iphone_17_plus_redirects_to_air(self) -> None:
        tags = build_fallback_tags("iphone 17 plus")
        self.assertIn("iPhone Air", tags.buscar)
        self.assertNotIn("17 Plus", tags.buscar)

    def test_repair_adds_safe_tags(self) -> None:
        fixed = repair_teteco_response("notebook dell", "Achei um preco incrivel por R$ 10,00")
        require_valid_teteco_response("notebook dell", fixed)
        self.assertIn("[BUSCAR: Notebook Dell Inspiron 15 Core i5 8GB SSD]", fixed)
        self.assertNotIn("R$ 10,00", fixed)

    def test_fallback_for_computer_uses_complete_desktop_terms(self) -> None:
        tags = build_fallback_tags("quero um computador barato")
        self.assertEqual(
            tags,
            SearchTags(
                "Computador Completo Intel Core i5 8GB SSD",
                "Desktop Completo Core i5 SSD",
                "Computador Completo",
            ),
        )

    def test_fallback_for_pc_gamer_uses_complete_pc_terms(self) -> None:
        tags = build_fallback_tags("pc gamer")
        self.assertEqual(tags.buscar_simples, "PC Gamer Completo")

    def test_rejects_pc_accessory_when_user_wants_computer(self) -> None:
        response = "\n".join(
            (
                "Boa!",
                "[BUSCAR: Cooler para PC Gamer RGB]",
                "[BUSCAR_ALT: Mouse Gamer para PC]",
                "[BUSCAR_SIMPLES: Monitor Gamer]",
            )
        )
        result = validate_teteco_response("quero computador", response)
        self.assertFalse(result.ok)
        self.assertIn("periferico", " ".join(result.errors))

    def test_rejects_console_accessory_when_user_wants_console(self) -> None:
        response = "\n".join(
            (
                "Boa!",
                "[BUSCAR: Controle Joystick para PS5]",
                "[BUSCAR_ALT: Controle PlayStation 5]",
                "[BUSCAR_SIMPLES: Controle PS5]",
            )
        )
        result = validate_teteco_response("quero ps5", response)
        self.assertFalse(result.ok)
        self.assertIn("acessorio", " ".join(result.errors))

    def test_rejects_tv_accessory_when_user_wants_tv(self) -> None:
        response = "\n".join(
            (
                "Boa!",
                "[BUSCAR: Suporte Articulado para Smart TV 55]",
                "[BUSCAR_ALT: Suporte TV 55]",
                "[BUSCAR_SIMPLES: Suporte TV]",
            )
        )
        result = validate_teteco_response("smart tv 55", response)
        self.assertFalse(result.ok)
        self.assertIn("acessorio", " ".join(result.errors))

    def test_rejects_air_conditioner_accessory_when_user_wants_air_conditioner(self) -> None:
        response = "\n".join(
            (
                "Boa!",
                "[BUSCAR: Controle para Ar Condicionado Split]",
                "[BUSCAR_ALT: Controle Ar Condicionado]",
                "[BUSCAR_SIMPLES: Controle Ar]",
            )
        )
        result = validate_teteco_response("ar condicionado split", response)
        self.assertFalse(result.ok)
        self.assertIn("acessorio", " ".join(result.errors))

    def test_accepts_complete_pc_when_user_wants_computer(self) -> None:
        response = "\n".join(
            (
                "Boa! Vou focar no computador completo.",
                "[BUSCAR: PC Gamer Completo Ryzen 5 16GB SSD]",
                "[BUSCAR_ALT: Computador Gamer Completo Ryzen 5]",
                "[BUSCAR_SIMPLES: PC Gamer Completo]",
            )
        )
        result = validate_teteco_response("quero computador gamer", response)
        self.assertTrue(result.ok, result.errors)

    def test_catalog_fallback_for_monitor(self) -> None:
        tags = build_fallback_tags("monitor gamer")
        self.assertEqual(tags.buscar_simples, "Monitor Gamer")

    def test_monitor_for_pc_is_monitor_intent_not_computer_intent(self) -> None:
        tags = build_fallback_tags("monitor para pc")
        self.assertEqual(tags.buscar_simples, "Monitor Gamer")

    def test_generic_rejects_accessory_tags_for_unknown_product(self) -> None:
        response = "\n".join(
            (
                "Boa!",
                "[BUSCAR: Rodinha para Cadeira de Escritorio]",
                "[BUSCAR_ALT: Peca Reposicao Cadeira]",
                "[BUSCAR_SIMPLES: Rodinha Cadeira]",
            )
        )
        result = validate_teteco_response("cadeira ergonomica", response)
        self.assertFalse(result.ok)
        self.assertIn("acessorio", " ".join(result.errors))

    def test_generic_rejects_unrelated_tags_for_unknown_product(self) -> None:
        response = "\n".join(
            (
                "Boa!",
                "[BUSCAR: Garrafa Termica Inox]",
                "[BUSCAR_ALT: Copo Termico]",
                "[BUSCAR_SIMPLES: Garrafa Termica]",
            )
        )
        result = validate_teteco_response("mochila escolar", response)
        self.assertFalse(result.ok)
        self.assertIn("aderencia", " ".join(result.errors))

    def test_generic_accepts_matching_tags_for_unknown_product(self) -> None:
        response = "\n".join(
            (
                "Boa!",
                "[BUSCAR: Furadeira Bosch Impacto 650W]",
                "[BUSCAR_ALT: Furadeira Bosch 650W]",
                "[BUSCAR_SIMPLES: Furadeira Bosch]",
            )
        )
        result = validate_teteco_response("furadeira bosch", response)
        self.assertTrue(result.ok, result.errors)

    def test_explicit_accessory_request_allows_accessory_tags(self) -> None:
        response = "\n".join(
            (
                "Boa!",
                "[BUSCAR: Capa iPhone 17 Silicone]",
                "[BUSCAR_ALT: Capinha iPhone 17]",
                "[BUSCAR_SIMPLES: Capa iPhone]",
            )
        )
        result = validate_teteco_response("capa para iphone 17", response)
        self.assertTrue(result.ok, result.errors)

    def test_generic_fallback_has_three_tags(self) -> None:
        tags = build_fallback_tags("cadeira ergonomica")
        self.assertEqual(len(tags.as_lines().splitlines()), 3)


if __name__ == "__main__":
    unittest.main()
