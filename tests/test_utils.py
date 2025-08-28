"""Tests for the utils module."""

import os
from pathlib import Path
from unittest.mock import patch

from rich.console import Console

from specsmith_cli.utils import (
    check_file_exists,
    confirm_overwrite,
    confirm_save,
    ensure_directory_exists,
    get_current_directory,
    get_file_extension,
    get_home_directory,
    is_debug_mode,
    print_error,
    print_info,
    print_success,
    print_warning,
    read_file_safely,
    safe_filename,
    suggest_filename,
    write_file_safely,
)


class TestDirectoryOperations:
    """Test cases for directory operations."""

    def test_get_current_directory(self):
        """Test getting current directory."""
        result = get_current_directory()
        assert isinstance(result, Path)
        assert result == Path.cwd()

    def test_get_home_directory(self):
        """Test getting home directory."""
        result = get_home_directory()
        assert isinstance(result, Path)
        assert result == Path.home()

    def test_ensure_directory_exists_new_directory(self, tmp_path):
        """Test creating a new directory."""
        new_dir = tmp_path / "new" / "nested" / "directory"
        assert not new_dir.exists()

        ensure_directory_exists(new_dir)

        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_ensure_directory_exists_existing_directory(self, tmp_path):
        """Test with existing directory."""
        existing_dir = tmp_path / "existing"
        existing_dir.mkdir()

        # Should not raise an error
        ensure_directory_exists(existing_dir)

        assert existing_dir.exists()
        assert existing_dir.is_dir()


class TestFileOperations:
    """Test cases for file operations."""

    def test_check_file_exists_true(self, tmp_path):
        """Test checking existing file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        # Change to tmp_path directory
        original_cwd = Path.cwd()
        os.chdir(tmp_path)
        try:
            result = check_file_exists("test.txt")
            assert result is True
        finally:
            os.chdir(original_cwd)

    def test_check_file_exists_false(self, tmp_path):
        """Test checking non-existent file."""
        # Change to tmp_path directory
        original_cwd = Path.cwd()
        os.chdir(tmp_path)
        try:
            result = check_file_exists("nonexistent.txt")
            assert result is False
        finally:
            os.chdir(original_cwd)

    def test_get_file_extension_with_extension(self):
        """Test getting file extension."""
        assert get_file_extension("test.txt") == ".txt"
        assert get_file_extension("document.pdf") == ".pdf"
        assert get_file_extension("archive.tar.gz") == ".gz"

    def test_get_file_extension_no_extension(self):
        """Test getting file extension for file without extension."""
        assert get_file_extension("README") == ""
        assert get_file_extension("Makefile") == ""

    def test_write_file_safely_success(self, tmp_path):
        """Test successful file writing."""
        test_file = tmp_path / "test.txt"
        content = "Hello, World!"

        result = write_file_safely(test_file, content)

        assert result is True
        assert test_file.exists()
        assert test_file.read_text(encoding="utf-8") == content

    def test_write_file_safely_with_nested_directory(self, tmp_path):
        """Test writing file with nested directory creation."""
        nested_file = tmp_path / "nested" / "deep" / "test.txt"
        content = "Nested content"

        result = write_file_safely(nested_file, content)

        assert result is True
        assert nested_file.exists()
        assert nested_file.read_text(encoding="utf-8") == content

    def test_write_file_safely_failure(self):
        """Test file writing failure."""
        # Try to write to an invalid path
        invalid_path = Path("/invalid/path/test.txt")
        content = "This should fail"

        with patch("specsmith_cli.utils.print_error") as mock_print_error:
            result = write_file_safely(invalid_path, content)

            assert result is False
            mock_print_error.assert_called_once()
            # Check that error message contains the path
            error_call = mock_print_error.call_args[0][0]
            assert str(invalid_path) in error_call

    def test_read_file_safely_success(self, tmp_path):
        """Test successful file reading."""
        test_file = tmp_path / "test.txt"
        content = "Hello, World!"
        test_file.write_text(content, encoding="utf-8")

        result = read_file_safely(test_file)

        assert result == content

    def test_read_file_safely_failure(self):
        """Test file reading failure."""
        nonexistent_file = Path("/nonexistent/file.txt")

        with patch("specsmith_cli.utils.print_error") as mock_print_error:
            result = read_file_safely(nonexistent_file)

            assert result is None
            mock_print_error.assert_called_once()
            # Check that error message contains the path
            error_call = mock_print_error.call_args[0][0]
            assert str(nonexistent_file) in error_call


class TestFilenameOperations:
    """Test cases for filename operations."""

    def test_safe_filename_basic(self):
        """Test basic filename sanitization."""
        assert safe_filename("normal_file.txt") == "normal_file.txt"
        assert safe_filename("file with spaces.txt") == "file with spaces.txt"

    def test_safe_filename_unsafe_characters(self):
        """Test sanitizing unsafe characters."""
        unsafe_chars = '<>:"/\\|?*'
        for char in unsafe_chars:
            filename = f"file{char}name.txt"
            result = safe_filename(filename)
            assert char not in result
            assert result == "file_name.txt"

    def test_safe_filename_leading_trailing_cleanup(self):
        """Test cleaning leading/trailing spaces and dots."""
        assert safe_filename("  file.txt  ") == "file.txt"
        assert safe_filename("..file.txt..") == "file.txt"
        assert safe_filename(" . file.txt . ") == "file.txt"

    def test_safe_filename_empty_input(self):
        """Test handling empty filename."""
        assert safe_filename("") == "untitled"
        assert safe_filename("   ") == "untitled"
        assert safe_filename("...") == "untitled"

    def test_suggest_filename_basic(self):
        """Test basic filename suggestion."""
        result = suggest_filename("test", ".py")
        assert result == "test.py"

    def test_suggest_filename_no_extension(self):
        """Test filename suggestion without extension."""
        result = suggest_filename("test")
        assert result == "test.txt"

    def test_suggest_filename_long_name(self):
        """Test filename suggestion with long name."""
        long_name = "a" * 60  # 60 characters
        result = suggest_filename(long_name, ".py")

        # Should be truncated to 50 characters plus extension
        assert len(result) == 53  # 50 + ".py"
        assert result.endswith(".py")
        assert result.startswith("a" * 50)

    def test_suggest_filename_unsafe_characters(self):
        """Test filename suggestion with unsafe characters."""
        unsafe_name = "file<>name"
        result = suggest_filename(unsafe_name, ".txt")

        assert result == "file__name.txt"


class TestDebugMode:
    """Test cases for debug mode detection."""

    def test_is_debug_mode_true_values(self):
        """Test debug mode with true values."""
        true_values = ["1", "true", "yes", "TRUE", "YES", "True"]

        for value in true_values:
            with patch.dict(os.environ, {"SPECSMITH_DEBUG": value}):
                assert is_debug_mode() is True

    def test_is_debug_mode_false_values(self):
        """Test debug mode with false values."""
        false_values = ["0", "false", "no", "FALSE", "NO", "False", ""]

        for value in false_values:
            with patch.dict(os.environ, {"SPECSMITH_DEBUG": value}):
                assert is_debug_mode() is False

    def test_is_debug_mode_no_env_var(self):
        """Test debug mode when environment variable is not set."""
        with patch.dict(os.environ, {}, clear=True):
            # Remove SPECSMITH_DEBUG if it exists
            if "SPECSMITH_DEBUG" in os.environ:
                del os.environ["SPECSMITH_DEBUG"]
            assert is_debug_mode() is False


class TestPrintFunctions:
    """Test cases for print utility functions."""

    def test_print_error(self):
        """Test error message printing."""
        with patch("specsmith_cli.utils.console") as mock_console:
            print_error("Test error message")

            mock_console.print.assert_called_once_with(
                "[red]❌ Test error message[/red]"
            )

    def test_print_success(self):
        """Test success message printing."""
        with patch("specsmith_cli.utils.console") as mock_console:
            print_success("Test success message")

            mock_console.print.assert_called_once_with(
                "[green]✅ Test success message[/green]"
            )

    def test_print_warning(self):
        """Test warning message printing."""
        with patch("specsmith_cli.utils.console") as mock_console:
            print_warning("Test warning message")

            mock_console.print.assert_called_once_with(
                "[yellow]⚠️  Test warning message[/yellow]"
            )

    def test_print_info(self):
        """Test info message printing."""
        with patch("specsmith_cli.utils.console") as mock_console:
            print_info("Test info message")

            mock_console.print.assert_called_once_with(
                "[blue]ℹ️  Test info message[/blue]"
            )


class TestConfirmationFunctions:
    """Test cases for user confirmation functions."""

    def test_confirm_overwrite_true(self):
        """Test file overwrite confirmation - user says yes."""
        with patch("rich.prompt.Confirm.ask", return_value=True) as mock_confirm:
            result = confirm_overwrite("test.txt")

            assert result is True
            mock_confirm.assert_called_once_with(
                "File 'test.txt' already exists. Do you want to overwrite it?",
                default=False,
            )

    def test_confirm_overwrite_false(self):
        """Test file overwrite confirmation - user says no."""
        with patch("rich.prompt.Confirm.ask", return_value=False) as mock_confirm:
            result = confirm_overwrite("test.txt")

            assert result is False
            mock_confirm.assert_called_once_with(
                "File 'test.txt' already exists. Do you want to overwrite it?",
                default=False,
            )

    def test_confirm_save_true(self):
        """Test file save confirmation - user says yes."""
        with patch("rich.prompt.Confirm.ask", return_value=True) as mock_confirm:
            result = confirm_save("test.txt")

            assert result is True
            mock_confirm.assert_called_once_with("Save file 'test.txt'?", default=True)

    def test_confirm_save_false(self):
        """Test file save confirmation - user says no."""
        with patch("rich.prompt.Confirm.ask", return_value=False) as mock_confirm:
            result = confirm_save("test.txt")

            assert result is False
            mock_confirm.assert_called_once_with("Save file 'test.txt'?", default=True)


class TestConsoleInstance:
    """Test cases for console instance."""

    def test_console_is_console_instance(self):
        """Test that console is a Console instance."""
        from specsmith_cli.utils import console

        assert isinstance(console, Console)


class TestIntegrationScenarios:
    """Test cases for integrated utility scenarios."""

    def test_safe_file_workflow(self, tmp_path):
        """Test complete safe file workflow."""
        # Create a filename with unsafe characters
        unsafe_name = "my<file>name"
        safe_name = safe_filename(unsafe_name)
        suggested_name = suggest_filename(safe_name, ".py")

        # Write file safely
        file_path = tmp_path / suggested_name
        content = "print('Hello, World!')"

        write_success = write_file_safely(file_path, content)
        assert write_success is True

        # Read file safely
        read_content = read_file_safely(file_path)
        assert read_content == content

        # Check file exists
        original_cwd = Path.cwd()
        os.chdir(tmp_path)
        try:
            file_exists = check_file_exists(suggested_name)
            assert file_exists is True
        finally:
            os.chdir(original_cwd)

    def test_directory_and_file_creation_workflow(self, tmp_path):
        """Test workflow with directory creation and file operations."""
        # Create nested directory structure
        nested_dir = tmp_path / "project" / "src" / "utils"
        ensure_directory_exists(nested_dir)

        # Create file in nested directory
        file_path = nested_dir / "helper.py"
        content = "def helper_function():\n    pass"

        success = write_file_safely(file_path, content)
        assert success is True

        # Verify file was created correctly
        assert file_path.exists()
        assert file_path.is_file()
        assert read_file_safely(file_path) == content

    def test_error_handling_workflow(self):
        """Test error handling in file operations."""
        # Test writing to invalid location
        invalid_path = Path("/root/restricted/file.txt")  # Typically restricted

        with patch("specsmith_cli.utils.print_error") as mock_print_error:
            write_result = write_file_safely(invalid_path, "content")
            assert write_result is False
            mock_print_error.assert_called_once()

        # Test reading non-existent file
        nonexistent_path = Path("/nonexistent/directory/file.txt")

        with patch("specsmith_cli.utils.print_error") as mock_print_error:
            read_result = read_file_safely(nonexistent_path)
            assert read_result is None
            mock_print_error.assert_called_once()

    def test_filename_sanitization_edge_cases(self):
        """Test edge cases in filename sanitization."""
        # Test various problematic filenames
        test_cases = [
            ("", "untitled"),
            ("   ", "untitled"),
            ("...", "untitled"),
            (
                "CON",
                "CON",
            ),  # Windows reserved name, but our function doesn't handle this
            ("file.txt.", "file.txt"),
            (".hidden", "hidden"),
            ("file\x00name", "file\x00name"),  # Null byte - not handled by our function
        ]

        for input_name, expected in test_cases:
            result = safe_filename(input_name)
            assert result == expected, f"Failed for input: {input_name!r}"

    def test_extension_handling_edge_cases(self):
        """Test edge cases in file extension handling."""
        test_cases = [
            ("file", ""),
            ("file.", ""),  # Path.suffix returns empty string for trailing dot
            (".hidden", ""),
            (".hidden.txt", ".txt"),
            ("file.tar.gz", ".gz"),
            ("file..txt", ".txt"),
        ]

        for filename, expected_ext in test_cases:
            result = get_file_extension(filename)
            assert result == expected_ext, f"Failed for filename: {filename}"
