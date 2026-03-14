"""
MCP Server for BigAGI Context Management.
Provides file-based memory system with tools for project management.
"""
import os
from pathlib import Path
from typing import Optional
from fastmcp import FastMCP

# Initialize MCP server
mcp = FastMCP("BigAGI Context Management")

# Base directory for all projects
BASE_DIR = Path.home() / "BigAGI_Projects"
BASE_DIR.mkdir(exist_ok=True)


def get_project_path(chat_id: str) -> Path:
    """Get path to project directory"""
    return BASE_DIR / chat_id


def validate_path(path: Path, chat_id: str) -> None:
    """Validate that path is within project directory"""
    project_path = get_project_path(chat_id)
    try:
        path.resolve().relative_to(project_path.resolve())
    except ValueError:
        raise ValueError(f"Path {path} is outside project directory")


@mcp.tool()
def create_project(chat_id: str) -> str:
    """
    Create a new project directory structure.

    Args:
        chat_id: Unique chat identifier

    Returns:
        Success message with created paths
    """
    project_path = get_project_path(chat_id)

    if project_path.exists():
        return f"Project already exists at {project_path}"

    # Create directory structure
    project_path.mkdir(parents=True)
    (project_path / "memory" / "topics").mkdir(parents=True)
    (project_path / "compression_history").mkdir(parents=True)

    # Create initial CLAUDE.md
    claude_md = project_path / "CLAUDE.md"
    claude_md.write_text("""# Project Rules

This file contains project-specific rules and architectural principles.

## Guidelines

- Add project-specific conventions here
- Document architectural decisions
- Keep this file under 5k tokens

""")

    # Create initial MEMORY.md
    memory_md = project_path / "MEMORY.md"
    memory_md.write_text("""# 🧠 Project Memory Index

## 📍 Current Active Context
- Main goal: [To be defined]
- Current stage: [To be defined]
- Next step: [To be defined]

## 🗂️ Pointers to Detailed Knowledge
[No topics yet]

## ⚠️ Critical Rules and Past Errors (Gotchas)
[No gotchas yet]

## 📋 Global Decision Log
[No decisions yet]

""")

    return f"""Project created successfully at {project_path}
Created:
- {claude_md}
- {memory_md}
- {project_path / 'memory' / 'topics'}
- {project_path / 'compression_history'}
"""


@mcp.tool()
def read_file(chat_id: str, file_path: str) -> str:
    """
    Read a file from the project.

    Args:
        chat_id: Project identifier
        file_path: Relative path within project (e.g., "MEMORY.md" or "memory/topics/architecture.md")

    Returns:
        File contents
    """
    project_path = get_project_path(chat_id)
    full_path = project_path / file_path

    validate_path(full_path, chat_id)

    if not full_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if not full_path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")

    return full_path.read_text()


@mcp.tool()
def write_file(chat_id: str, file_path: str, content: str) -> str:
    """
    Write or overwrite a file in the project.

    Args:
        chat_id: Project identifier
        file_path: Relative path within project
        content: File content

    Returns:
        Success message
    """
    project_path = get_project_path(chat_id)
    full_path = project_path / file_path

    validate_path(full_path, chat_id)

    # Create parent directories if needed
    full_path.parent.mkdir(parents=True, exist_ok=True)

    full_path.write_text(content)

    return f"File written successfully: {file_path} ({len(content)} chars)"


@mcp.tool()
def edit_file(chat_id: str, file_path: str, old_text: str, new_text: str) -> str:
    """
    Edit a file by replacing old_text with new_text.

    Args:
        chat_id: Project identifier
        file_path: Relative path within project
        old_text: Text to find and replace
        new_text: Replacement text

    Returns:
        Success message
    """
    project_path = get_project_path(chat_id)
    full_path = project_path / file_path

    validate_path(full_path, chat_id)

    if not full_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    content = full_path.read_text()

    if old_text not in content:
        raise ValueError(f"Text not found in file: {old_text[:50]}...")

    # Count occurrences
    count = content.count(old_text)
    if count > 1:
        raise ValueError(f"Text appears {count} times in file. Use write_file for multiple replacements.")

    new_content = content.replace(old_text, new_text)
    full_path.write_text(new_content)

    return f"File edited successfully: {file_path}"


@mcp.tool()
def list_files(chat_id: str, directory: str = ".") -> str:
    """
    List files in a project directory.

    Args:
        chat_id: Project identifier
        directory: Relative directory path (default: root)

    Returns:
        List of files and directories
    """
    project_path = get_project_path(chat_id)
    full_path = project_path / directory

    validate_path(full_path, chat_id)

    if not full_path.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")

    if not full_path.is_dir():
        raise ValueError(f"Path is not a directory: {directory}")

    items = []
    for item in sorted(full_path.iterdir()):
        rel_path = item.relative_to(project_path)
        if item.is_dir():
            items.append(f"📁 {rel_path}/")
        else:
            size = item.stat().st_size
            items.append(f"📄 {rel_path} ({size} bytes)")

    return "\n".join(items) if items else "[Empty directory]"


@mcp.tool()
def delete_file(chat_id: str, file_path: str) -> str:
    """
    Delete a file from the project.

    Args:
        chat_id: Project identifier
        file_path: Relative path within project

    Returns:
        Success message
    """
    project_path = get_project_path(chat_id)
    full_path = project_path / file_path

    validate_path(full_path, chat_id)

    if not full_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if full_path.is_dir():
        raise ValueError(f"Path is a directory, not a file: {file_path}")

    full_path.unlink()

    return f"File deleted successfully: {file_path}"


if __name__ == "__main__":
    # Run MCP server
    mcp.run()
