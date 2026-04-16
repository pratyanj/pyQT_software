import unittest

from core.enums import ProductKind, WindowType
from core.models import WindowModel
from core.profile_library import get_profile, list_profiles
from core.validator import Validator
from engine.generator import FrontViewGenerator
from engine.cross_section import CrossSectionGenerator
from engine.generator_3d import Generator3D


class FenestrationProfileTests(unittest.TestCase):
    def _model_from_profile(
        self,
        profile_key: str,
        product_kind: ProductKind,
        window_type: WindowType,
        width: float,
        height: float,
    ) -> WindowModel:
        profile = get_profile(profile_key)
        self.assertIsNotNone(profile)
        return WindowModel(
            product_kind=product_kind,
            window_type=window_type,
            profile_key=profile_key,
            width=width,
            height=height,
            frame_width=profile.frame_width,
            frame_depth=profile.frame_depth,
            glass_thickness=profile.default_glass_thickness,
            num_panels=profile.default_panels,
            mullion_width=profile.mullion_width,
            threshold_height=profile.threshold_height,
        )

    def test_window_profile_validates(self):
        model = self._model_from_profile(
            "win_basic_50",
            ProductKind.WINDOW,
            WindowType.SLIDING,
            1800.0,
            1400.0,
        )
        self.assertEqual(Validator.validate(model), [])

    def test_door_profile_validates(self):
        model = self._model_from_profile(
            "door_swing_75",
            ProductKind.DOOR,
            WindowType.SINGLE_SWING_DOOR,
            1100.0,
            2200.0,
        )
        self.assertEqual(Validator.validate(model), [])

    def test_generators_return_shapes_for_door(self):
        model = self._model_from_profile(
            "door_slide_90",
            ProductKind.DOOR,
            WindowType.SLIDING,
            2600.0,
            2400.0,
        )
        front = FrontViewGenerator().generate(model)
        hsec = CrossSectionGenerator().generate_horizontal(model)
        vsec = CrossSectionGenerator().generate_vertical(model)
        view3d = Generator3D().generate(model)

        self.assertGreater(len(front), 0)
        self.assertGreater(len(hsec), 0)
        self.assertGreater(len(vsec), 0)
        self.assertGreater(len(view3d), 0)

    def test_custom_profile_from_json_is_available(self):
        profiles = list_profiles(ProductKind.WINDOW, WindowType.SLIDING)
        keys = {p.key for p in profiles}
        self.assertIn("custom_window_multichamber_78", keys)

    def test_custom_profile_features_render_in_section(self):
        model = self._model_from_profile(
            "custom_window_multichamber_78",
            ProductKind.WINDOW,
            WindowType.SLIDING,
            2200.0,
            1500.0,
        )
        hsec = CrossSectionGenerator().generate_horizontal(model)
        layers = {s.get("layer") for s in hsec if s.get("type") == "rect"}
        self.assertIn("cavity", layers)
        self.assertIn("reinforcement", layers)


if __name__ == "__main__":
    unittest.main()
