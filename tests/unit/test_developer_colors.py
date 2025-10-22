"""Tests for developer color mapping system."""
import pytest
from src.data.developer_colors import DeveloperColorMapper


def test_color_mapper_initialization():
    """Test color mapper initializes with config."""
    mapper = DeveloperColorMapper("config/developer_names.json")
    assert mapper is not None


def test_get_color_for_developer():
    """Test getting consistent color for developer."""
    mapper = DeveloperColorMapper("config/developer_names.json")

    color1 = mapper.get_color("Chad Walters")
    color2 = mapper.get_color("Chad Walters")

    assert color1 == color2
    assert isinstance(color1, str)
    assert color1.startswith("#")


def test_get_color_map():
    """Test getting full color map."""
    mapper = DeveloperColorMapper("config/developer_names.json")

    color_map = mapper.get_color_map(["Chad Walters", "EJ", "JP"])

    assert len(color_map) == 3
    assert "Chad Walters" in color_map
    assert "EJ" in color_map
    assert "JP" in color_map
    assert all(c.startswith("#") for c in color_map.values())


def test_colors_are_consistent_across_instances():
    """Test colors remain consistent across instances."""
    mapper1 = DeveloperColorMapper("config/developer_names.json")
    mapper2 = DeveloperColorMapper("config/developer_names.json")

    color1 = mapper1.get_color("Chad Walters")
    color2 = mapper2.get_color("Chad Walters")

    assert color1 == color2


def test_no_color_collisions_for_known_developers():
    """Test that all known developers have unique colors (no hash collisions)."""
    mapper = DeveloperColorMapper("config/developer_names.json")

    # Get colors for all known developers
    known_developers = ["Chad Walters", "EJ", "Jeremiah", "JP", "Matt Kindy"]
    colors = [mapper.get_color(dev) for dev in known_developers]

    # Verify all colors are unique (no collisions)
    assert len(colors) == len(set(colors)), (
        f"Color collision detected! {len(known_developers)} developers "
        f"but only {len(set(colors))} unique colors: {dict(zip(known_developers, colors))}"
    )
