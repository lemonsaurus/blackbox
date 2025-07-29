"""
Tests for Docker version tagging logic used in GitHub Actions workflows.

This module tests the version parsing logic that extracts major, minor, and patch
versions from release tags for Docker image tagging.
"""

import pytest


class TestDockerVersionTags:
    """Test Docker version tag parsing logic."""

    def parse_version_tags(self, tag_name: str) -> dict:
        """
        Simulate the version parsing logic from the GitHub Actions workflow.

        Args:
            tag_name: The release tag name (e.g., 'v3.1.2')

        Returns:
            Dictionary with parsed version components
        """
        # Remove 'v' prefix if present
        version = tag_name[1:] if tag_name.startswith('v') else tag_name

        # Split version into parts
        version_parts = version.split('.')
        major = version_parts[0]
        minor = version_parts[1] if len(version_parts) > 1 else '0'

        return {
            'full_version': tag_name,
            'major_minor': f'v{major}.{minor}',
            'major': f'v{major}'
        }

    def test_standard_semver_parsing(self):
        """Test parsing of standard semantic version tags."""
        result = self.parse_version_tags('v3.1.2')

        assert result['full_version'] == 'v3.1.2'
        assert result['major_minor'] == 'v3.1'
        assert result['major'] == 'v3'

    def test_major_version_only(self):
        """Test parsing when only major version is provided."""
        result = self.parse_version_tags('v5')

        assert result['full_version'] == 'v5'
        assert result['major_minor'] == 'v5.0'
        assert result['major'] == 'v5'

    def test_major_minor_only(self):
        """Test parsing when only major.minor version is provided."""
        result = self.parse_version_tags('v2.0')

        assert result['full_version'] == 'v2.0'
        assert result['major_minor'] == 'v2.0'
        assert result['major'] == 'v2'

    def test_double_digit_versions(self):
        """Test parsing with double-digit version numbers."""
        result = self.parse_version_tags('v10.15.3')

        assert result['full_version'] == 'v10.15.3'
        assert result['major_minor'] == 'v10.15'
        assert result['major'] == 'v10'

    def test_without_v_prefix(self):
        """Test parsing version tags without 'v' prefix."""
        result = self.parse_version_tags('2.0.5')

        assert result['full_version'] == '2.0.5'
        assert result['major_minor'] == 'v2.0'
        assert result['major'] == 'v2'

    def test_zero_versions(self):
        """Test parsing with zero in version components."""
        result = self.parse_version_tags('v1.0.0')

        assert result['full_version'] == 'v1.0.0'
        assert result['major_minor'] == 'v1.0'
        assert result['major'] == 'v1'

    @pytest.mark.parametrize(
        "tag_name,expected_full,expected_major_minor,expected_major", [
            ('v3.1.2', 'v3.1.2', 'v3.1', 'v3'),
            ('v2.0.5', 'v2.0.5', 'v2.0', 'v2'),
            ('v10.15.3', 'v10.15.3', 'v10.15', 'v10'),
            ('v1.0.0', 'v1.0.0', 'v1.0', 'v1'),
            ('v0.1.0', 'v0.1.0', 'v0.1', 'v0'),
            ('v4.2.1', 'v4.2.1', 'v4.2', 'v4'),
        ])
    def test_version_parsing_parametrized(
            self, tag_name, expected_full, expected_major_minor, expected_major):
        """Parametrized test for various version tag formats."""
        result = self.parse_version_tags(tag_name)

        assert result['full_version'] == expected_full
        assert result['major_minor'] == expected_major_minor
        assert result['major'] == expected_major

    def test_docker_tags_generation(self):
        """Test that generated Docker tags match expected format."""
        result = self.parse_version_tags('v3.1.2')

        # Simulate Docker tags that would be generated
        expected_tags = [
            'lemonsaurus/blackbox:latest',
            f'lemonsaurus/blackbox:{result["full_version"]}',
            f'lemonsaurus/blackbox:{result["major_minor"]}',
            f'lemonsaurus/blackbox:{result["major"]}'
        ]

        full_tag = f'lemonsaurus/blackbox:{result["full_version"]}'
        minor_tag = f'lemonsaurus/blackbox:{result["major_minor"]}'
        major_tag = f'lemonsaurus/blackbox:{result["major"]}'

        assert full_tag == 'lemonsaurus/blackbox:v3.1.2'
        assert minor_tag == 'lemonsaurus/blackbox:v3.1'
        assert major_tag == 'lemonsaurus/blackbox:v3'
        assert len(expected_tags) == 4  # latest + full + major.minor + major
