import unittest

from src.components.locale_detection import detect_locale_overlay_domain


class DetectLocaleOverlayDomainTests(unittest.TestCase):
    def test_empty_or_missing_layers_returns_base_only(self) -> None:
        self.assertEqual(detect_locale_overlay_domain(""), [])
        self.assertEqual(detect_locale_overlay_domain(None), [])
        self.assertEqual(detect_locale_overlay_domain("   "), [])

    def test_layers_with_no_locale_entry_returns_base_only(self) -> None:
        self.assertEqual(detect_locale_overlay_domain("src/core"), [])

    def test_picks_region_specific_locale(self) -> None:
        self.assertEqual(
            detect_locale_overlay_domain("src/core src/locales/en/US"),
            ["src/locales/en/US/domain"],
        )

    def test_prefers_most_specific_when_both_present(self) -> None:
        self.assertEqual(
            detect_locale_overlay_domain("src/core src/locales/cs src/locales/cs/CZ"),
            ["src/locales/cs/CZ/domain"],
        )

    def test_language_only_no_region(self) -> None:
        self.assertEqual(
            detect_locale_overlay_domain("src/core src/locales/fr"),
            ["src/locales/fr/domain"],
        )

    def test_reads_real_env_var_when_no_explicit_value_given(self) -> None:
        import os
        from unittest import mock

        with mock.patch.dict(os.environ, {"LAYERS": "src/core src/locales/el/GR"}, clear=False):
            self.assertEqual(detect_locale_overlay_domain(), ["src/locales/el/GR/domain"])


if __name__ == "__main__":
    unittest.main()
