"""Test exit code behavior for CLI operations."""
from unittest.mock import Mock
from unittest.mock import patch

from blackbox.cli import run


class TestCLIExitCodes:
    """Test that CLI exits with proper codes on failures."""

    def test_successful_backup_returns_true(self, config_file):
        """Test that successful backups return True from run()."""
        with patch('blackbox.utils.workflows.get_configured_handlers') as mock_get_handlers:
            # Mock successful database handler
            mock_db = Mock()
            mock_db.config = {'id': 'test_db'}
            mock_db.backup_extension = '.sql'
            mock_db.success = True
            mock_db.output = 'Success'
            mock_db.get_id_for_retention.return_value = 'test_db'

            # Mock successful storage handler
            mock_storage = Mock()
            mock_storage.config = {'id': 'test_storage'}
            mock_storage.success = True
            mock_storage.output = 'Uploaded successfully'

            # Mock workflow
            mock_workflow = Mock()
            mock_workflow.database = mock_db
            mock_workflow.storage_providers = [mock_storage]
            mock_workflow.notifiers = []

            mock_get_handlers.side_effect = [
                {'test_db': mock_db},
                {'test_storage': mock_storage},
                {'all': []}
            ]

            with patch('blackbox.utils.workflows.get_workflows', return_value=[mock_workflow]):
                result = run()

            assert result is True
            assert mock_db.backup.called
            assert mock_storage.sync.called

    def test_database_failure_returns_false(self, config_file):
        """Test that database backup failures cause run() to return False."""
        with patch('blackbox.utils.workflows.get_configured_handlers') as mock_get_handlers:
            # Mock failed database handler
            mock_db = Mock()
            mock_db.config = {'id': 'test_db'}
            mock_db.backup_extension = '.sql'
            mock_db.success = False
            mock_db.output = 'Database connection failed'
            mock_db.get_id_for_retention.return_value = 'test_db'

            # Mock storage handler (won't be called due to database failure)
            mock_storage = Mock()
            mock_storage.config = {'id': 'test_storage'}
            mock_storage.success = True
            mock_storage.output = 'Not called'

            # Mock workflow
            mock_workflow = Mock()
            mock_workflow.database = mock_db
            mock_workflow.storage_providers = [mock_storage]
            mock_workflow.notifiers = []

            mock_get_handlers.side_effect = [
                {'test_db': mock_db},
                {'test_storage': mock_storage},
                {'all': []}
            ]

            with patch('blackbox.utils.workflows.get_workflows', return_value=[mock_workflow]):
                result = run()

            assert result is False
            assert mock_db.backup.called
            assert not mock_storage.sync.called

    def test_storage_failure_returns_false(self, config_file):
        """Test that storage failures cause run() to return False."""
        with patch('blackbox.utils.workflows.get_configured_handlers') as mock_get_handlers:
            # Mock successful database handler
            mock_db = Mock()
            mock_db.config = {'id': 'test_db'}
            mock_db.backup_extension = '.sql'
            mock_db.success = True
            mock_db.output = 'Success'
            mock_db.get_id_for_retention.return_value = 'test_db'

            # Mock failed storage handler
            mock_storage = Mock()
            mock_storage.config = {'id': 'test_storage'}
            mock_storage.success = False
            mock_storage.output = 'Upload failed'

            # Mock workflow
            mock_workflow = Mock()
            mock_workflow.database = mock_db
            mock_workflow.storage_providers = [mock_storage]
            mock_workflow.notifiers = []

            mock_get_handlers.side_effect = [
                {'test_db': mock_db},
                {'test_storage': mock_storage},
                {'all': []}
            ]

            with patch('blackbox.utils.workflows.get_workflows', return_value=[mock_workflow]):
                result = run()

            assert result is False
            assert mock_db.backup.called
            assert mock_storage.sync.called

    def test_mixed_success_failure_returns_false(self, config_file):
        """Test that if any database fails, overall result is False."""
        with patch('blackbox.utils.workflows.get_configured_handlers') as mock_get_handlers:
            # Mock one successful and one failed database
            mock_db1 = Mock()
            mock_db1.config = {'id': 'db1'}
            mock_db1.backup_extension = '.sql'
            mock_db1.success = True
            mock_db1.output = 'Success'
            mock_db1.get_id_for_retention.return_value = 'db1'

            mock_db2 = Mock()
            mock_db2.config = {'id': 'db2'}
            mock_db2.backup_extension = '.sql'
            mock_db2.success = False
            mock_db2.output = 'Failed'
            mock_db2.get_id_for_retention.return_value = 'db2'

            # Mock storage handler
            mock_storage = Mock()
            mock_storage.config = {'id': 'test_storage'}
            mock_storage.success = True
            mock_storage.output = 'Success'

            # Mock workflows
            mock_workflow1 = Mock()
            mock_workflow1.database = mock_db1
            mock_workflow1.storage_providers = [mock_storage]
            mock_workflow1.notifiers = []

            mock_workflow2 = Mock()
            mock_workflow2.database = mock_db2
            mock_workflow2.storage_providers = [mock_storage]
            mock_workflow2.notifiers = []

            mock_get_handlers.side_effect = [
                {'db1': mock_db1, 'db2': mock_db2},
                {'test_storage': mock_storage},
                {'all': []}
            ]

            with patch('blackbox.utils.workflows.get_workflows',
                       return_value=[mock_workflow1, mock_workflow2]):
                result = run()

            assert result is False
            assert mock_db1.backup.called
            assert mock_db2.backup.called
            assert mock_storage.sync.call_count == 1
