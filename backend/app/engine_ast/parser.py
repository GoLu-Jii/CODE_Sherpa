"""
parser.py - File Traversal Logic for CODE_Sherpa
Recursively discovers Python source files while excluding common non-source directories.
"""

import os
from pathlib import Path
from typing import List, Set


class FileTraverser:
    """Handles recursive directory traversal and Python file discovery."""
    
    # Directories to exclude from traversal
    EXCLUDED_DIRS: Set[str] = {
        'venv',
        'env',
        '.venv',
        '__pycache__',
        '.git',
        '.svn',
        '.hg',
        'node_modules',
        '.pytest_cache',
        '.mypy_cache',
        '.tox',
        'build',
        'dist',
        'docs',
        'doc',
        'tests',
        'test',
        '.idea',
        '*.egg-info',
    }
    
    # File extensions to include
    INCLUDED_EXTENSIONS: Set[str] = {'.py'}
    
    def __init__(self, root_path: str):
        """
        Initialize the file traverser.
        
        Args:
            root_path: Root directory to start traversal from
        """
        self.root_path = Path(root_path).resolve()
        
        if not self.root_path.exists():
            raise ValueError(f"Path does not exist: {root_path}")
        
        if not self.root_path.is_dir():
            raise ValueError(f"Path is not a directory: {root_path}")
    
    def _should_exclude_dir(self, dir_name: str) -> bool:
        """
        Check if a directory should be excluded from traversal.
        
        Args:
            dir_name: Name of the directory to check
            
        Returns:
            True if directory should be excluded, False otherwise
        """
        # Check exact matches
        if dir_name in self.EXCLUDED_DIRS:
            return True
        
        # Check if it starts with a dot (hidden directories)
        if dir_name.startswith('.'):
            return True

        if dir_name.endswith('.egg-info'):
            return True
        
        return False
    
    def _is_valid_python_file(self, file_path: Path) -> bool:
        """
        Check if a file is a valid Python source file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if file should be included, False otherwise
        """
        # Check extension
        if file_path.suffix not in self.INCLUDED_EXTENSIONS:
            return False
        
        # Exclude files starting with dot
        if file_path.name.startswith('.'):
            return False
        
        # Check if file is readable
        if not os.access(file_path, os.R_OK):
            return False
        
        return True
    
    def traverse(self) -> List[str]:
        """
        Recursively traverse directory and collect Python files.
        
        Returns:
            List of relative paths to Python files from root_path
        """
        python_files = []
        
        for root, dirs, files in os.walk(self.root_path):
            # Convert to Path for easier manipulation
            root_path = Path(root)
            
            # Filter out excluded directories IN-PLACE
            # This prevents os.walk from descending into them
            dirs[:] = [
                d for d in dirs 
                if not self._should_exclude_dir(d)
            ]
            
            # Process files in current directory
            for file_name in files:
                file_path = root_path / file_name
                
                if self._is_valid_python_file(file_path):
                    # Get relative path from root
                    try:
                        relative_path = file_path.relative_to(self.root_path)
                        # Convert to string with forward slashes for consistency
                        python_files.append(str(relative_path).replace('\\', '/'))
                    except ValueError:
                        # Skip if file is not relative to root_path
                        continue
        
        # Sort for consistent ordering
        python_files.sort()
        
        return python_files


def get_python_files(repo_path: str) -> List[str]:
    """
    Convenience function to get all Python files in a repository.
    
    Args:
        repo_path: Path to the repository root
        
    Returns:
        List of relative paths to Python files
        
    Example:
        >>> files = get_python_files('./sample_repo')
        >>> print(files)
        ['app.py', 'service.py', 'utils/helper.py']
    """
    traverser = FileTraverser(repo_path)
    return traverser.traverse()


# CLI interface for testing
if __name__ == "__main__":
    import sys
    import json
    
    if len(sys.argv) < 2:
        print("Usage: python parser.py <repository_path>")
        sys.exit(1)
    
    repo_path = sys.argv[1]
    
    try:
        files = get_python_files(repo_path)
        print(json.dumps(files, indent=2))
        print(f"\nTotal Python files found: {len(files)}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
