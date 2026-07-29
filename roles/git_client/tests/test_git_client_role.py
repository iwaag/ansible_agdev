"""Static role contract checks for the nodeutils Git prerequisite."""

from pathlib import Path
import unittest


TASKS = Path(__file__).resolve().parents[1] / "tasks" / "main.yml"


class GitClientRoleTests(unittest.TestCase):
    def test_apt_refresh_precedes_generic_git_install_and_has_bounded_cache(self):
        text = TASKS.read_text()
        refresh = text.index("Refresh APT package cache before installing Git")
        install = text.index("Install Git packages")
        self.assertLess(refresh, install)
        self.assertIn("ansible.builtin.apt:", text[refresh:install])
        self.assertIn("update_cache: true", text[refresh:install])
        self.assertIn("cache_valid_time: 3600", text[refresh:install])

    def test_non_apt_hosts_skip_the_apt_specific_task(self):
        text = TASKS.read_text()
        refresh = text.index("Refresh APT package cache before installing Git")
        install = text.index("Install Git packages")
        self.assertIn('when: ansible_pkg_mgr == "apt"', text[refresh:install])
        self.assertIn("ansible.builtin.package:", text[install:])


if __name__ == "__main__":
    unittest.main()
