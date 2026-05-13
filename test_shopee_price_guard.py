from __future__ import annotations

import unittest
from decimal import Decimal

from shopee_price_guard import PriceValidationError, format_brl, parse_shopee_money, validate_shopee_offer


class ShopeePriceGuardTest(unittest.TestCase):
    def test_numeric_api_price_is_centavos_and_converted_once(self) -> None:
        self.assertEqual(parse_shopee_money(275700), Decimal("2757.00"))

    def test_formatted_price_text_is_not_divided_again(self) -> None:
        self.assertEqual(parse_shopee_money("R$ 2.757,00"), Decimal("2757.00"))

    def test_rejects_zero_price(self) -> None:
        with self.assertRaises(PriceValidationError):
            validate_shopee_offer(
                {
                    "productName": "Kit 10 Panos De Limpeza Microfibra",
                    "priceMin": 0,
                    "offerLink": "https://shopee.com.br/produto",
                }
            )

    def test_rejects_commission_used_as_price(self) -> None:
        with self.assertRaisesRegex(PriceValidationError, "commission"):
            validate_shopee_offer(
                {
                    "productName": "Ar Condicionado Split Hi Wall Inverter 18000 BTU",
                    "commission": "27.57",
                    "offerLink": "https://shopee.com.br/produto",
                }
            )

    def test_rejects_iphone_with_suspicious_low_price(self) -> None:
        with self.assertRaisesRegex(PriceValidationError, "Preco suspeito"):
            validate_shopee_offer(
                {
                    "productName": "Celular iPhone 16 Pro Max 256gb 5g Lacrado",
                    "priceMin": 8900,
                    "priceMax": 9700,
                }
            )

    def test_rejects_air_conditioner_with_suspicious_low_price(self) -> None:
        with self.assertRaisesRegex(PriceValidationError, "Preco suspeito"):
            validate_shopee_offer(
                {
                    "productName": "Ar Condicionado Split Midea Inverter 18000 BTU",
                    "priceMin": 2757,
                }
            )

    def test_accepts_valid_air_conditioner_price(self) -> None:
        offer = validate_shopee_offer(
            {
                "productName": "Ar Condicionado Split Midea Inverter 18000 BTU",
                "priceMin": 275700,
                "priceMax": 324800,
                "priceDiscountRate": 12,
                "shopName": "Loja Oficial",
            }
        )
        self.assertEqual(offer.price_text, "R$ 2.757,00 ~ R$ 3.248,00")

    def test_rejects_computer_accessory_when_request_is_computer(self) -> None:
        with self.assertRaisesRegex(PriceValidationError, "acessorio/periferico"):
            validate_shopee_offer(
                {
                    "productName": "Cooler Fan RGB para PC Gamer silencioso",
                    "priceMin": 5999,
                },
                user_request="quero um computador",
            )

    def test_rejects_monitor_when_request_is_computer(self) -> None:
        with self.assertRaisesRegex(PriceValidationError, "acessorio/periferico"):
            validate_shopee_offer(
                {
                    "productName": "Monitor Gamer 24 polegadas Full HD HDMI",
                    "priceMin": 49900,
                },
                user_request="computador gamer barato",
            )

    def test_accepts_complete_pc_when_request_is_computer(self) -> None:
        offer = validate_shopee_offer(
            {
                "productName": "PC Gamer Completo Ryzen 5 5600G 16GB SSD 480GB",
                "priceMin": 159900,
            },
            user_request="computador gamer",
        )
        self.assertEqual(offer.price_text, "R$ 1.599,00")

    def test_rejects_phone_accessory_when_request_is_phone(self) -> None:
        with self.assertRaisesRegex(PriceValidationError, "acessorio"):
            validate_shopee_offer(
                {
                    "productName": "Capa Case Transparente para iPhone 17 Pro Max",
                    "priceMin": 2990,
                },
                user_request="iphone 17",
            )

    def test_rejects_console_accessory_when_request_is_console(self) -> None:
        with self.assertRaisesRegex(PriceValidationError, "acessorio"):
            validate_shopee_offer(
                {
                    "productName": "Controle Joystick sem fio para PS5",
                    "priceMin": 19900,
                },
                user_request="ps5",
            )

    def test_rejects_tv_accessory_when_request_is_tv(self) -> None:
        with self.assertRaisesRegex(PriceValidationError, "acessorio"):
            validate_shopee_offer(
                {
                    "productName": "Suporte articulado para Smart TV 55 polegadas",
                    "priceMin": 8990,
                },
                user_request="smart tv 55",
            )

    def test_accepts_console_bundle_when_main_product_comes_first(self) -> None:
        offer = validate_shopee_offer(
            {
                "productName": "Console PlayStation 5 Slim Sony com Controle DualSense",
                "priceMin": 329900,
            },
            user_request="ps5",
        )
        self.assertEqual(offer.price_text, "R$ 3.299,00")

    def test_uses_search_term_as_intent_context(self) -> None:
        with self.assertRaisesRegex(PriceValidationError, "acessorio"):
            validate_shopee_offer(
                {
                    "productName": "Capinha Silicone para Samsung Galaxy S26",
                    "priceMin": 1990,
                },
                search_term="Samsung Galaxy S26",
            )

    def test_monitor_request_for_pc_accepts_monitor_as_main_product(self) -> None:
        offer = validate_shopee_offer(
            {
                "productName": "Monitor Gamer 24 polegadas Full HD HDMI",
                "priceMin": 49900,
            },
            user_request="monitor para pc",
        )
        self.assertEqual(offer.price_text, "R$ 499,00")

    def test_generic_rejects_chair_part_when_request_is_chair(self) -> None:
        with self.assertRaisesRegex(PriceValidationError, "acessorio/peca"):
            validate_shopee_offer(
                {
                    "productName": "Rodinha de Reposicao para Cadeira de Escritorio",
                    "priceMin": 2990,
                },
                user_request="cadeira ergonomica",
            )

    def test_generic_accepts_matching_chair(self) -> None:
        offer = validate_shopee_offer(
            {
                "productName": "Cadeira Ergonomica de Escritorio com Apoio Lombar",
                "priceMin": 49990,
            },
            user_request="cadeira ergonomica",
        )
        self.assertEqual(offer.price_text, "R$ 499,90")

    def test_generic_rejects_drill_accessory_when_request_is_drill(self) -> None:
        with self.assertRaisesRegex(PriceValidationError, "acessorio/peca"):
            validate_shopee_offer(
                {
                    "productName": "Kit Broca para Furadeira Bosch Madeira e Parede",
                    "priceMin": 3990,
                },
                user_request="furadeira bosch",
            )

    def test_generic_rejects_unrelated_result(self) -> None:
        with self.assertRaisesRegex(PriceValidationError, "aderencia"):
            validate_shopee_offer(
                {
                    "productName": "Garrafa Termica Inox 1 Litro",
                    "priceMin": 5990,
                },
                user_request="mochila escolar",
            )

    def test_explicit_accessory_request_still_allows_accessory(self) -> None:
        offer = validate_shopee_offer(
            {
                "productName": "Capa Transparente para iPhone 17 Pro Max",
                "priceMin": 2990,
            },
            user_request="capa para iphone 17",
        )
        self.assertEqual(offer.price_text, "R$ 29,90")

    def test_rejects_complete_computer_with_suspicious_low_price(self) -> None:
        with self.assertRaisesRegex(PriceValidationError, "Preco suspeito"):
            validate_shopee_offer(
                {
                    "productName": "Computador Completo Intel Core i5 8GB SSD",
                    "priceMin": 29900,
                },
                user_request="computador",
            )

    def test_accepts_cheap_cleaning_offer(self) -> None:
        offer = validate_shopee_offer(
            {
                "productName": "Kit 10 Panos De Limpeza Microfibra alta absorcao",
                "priceMin": 999,
                "priceDiscountRate": 15,
            }
        )
        self.assertEqual(offer.price_text, "R$ 9,99")

    def test_format_brl(self) -> None:
        self.assertEqual(format_brl(Decimal("1234.5")), "R$ 1.234,50")


if __name__ == "__main__":
    unittest.main()
