#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "rich",
#     "json5",
# ]
# ///

import json
import json5
import sys
import argparse
from pathlib import Path
from typing import Any
from rich.console import Console

console = Console()

def load_jsonc(file_path: Path) -> Any:
    """Load JSON/JSONC file using json5 to handle comments and trailing commas."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json5.load(f)

def pretty_print_json_file(file_path: Path) -> bool:
    """Read a JSON file and pretty print it to the console."""
    try:
        data = load_jsonc(file_path)
        
        # Print
        console.rule(f"[bold blue]{file_path.name}[/bold blue]")
        console.print_json(data=data)
        console.print("\n")
            
        return True
        
    except json.JSONDecodeError as e:
        console.print(f"[red]✗ Error parsing {file_path.name}[/red]: {e}")
        return False
    except Exception as e:
        console.print(f"[red]✗ Error processing {file_path.name}[/red]: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Pretty print JSON files.")
    parser.add_argument("paths", nargs="*", type=Path, help="Files or directories to pretty print")
    args = parser.parse_args()

    console.print(f"[bold]JSON Pretty Printer[/bold]")

    paths_to_process = args.paths

    # Default if no arguments provided
    if not paths_to_process:
        # Determine the project root relative to this script
        # Script is in /scripts/, so root is one level up
        script_dir = Path(__file__).resolve().parent
        project_root = script_dir.parent
        target_dir = project_root / "apps" / "repl-client" / "docs"
        console.print(f"[dim]No arguments provided. Using default directory:[/dim] [blue]{target_dir}[/blue]\n")
        
        if not target_dir.exists():
            console.print(f"[red]Default target directory does not exist![/red]")
            sys.exit(1)
        
        paths_to_process = [target_dir]

    json_files = []
    
    # Gather all files
    for path in paths_to_process:
        if path.is_file():
            json_files.append(path)
        elif path.is_dir():
            json_files.extend(list(path.rglob("*.json")) + list(path.rglob("*.jsonc")))
        else:
            console.print(f"[yellow]Warning: Path does not exist: {path}[/yellow]")

    if not json_files:
        console.print("[yellow]No .json files found.[/yellow]")
        return

    console.print(f"Found {len(json_files)} JSON files.\n")
    
    success_count = 0
    for file_path in json_files:
        if pretty_print_json_file(file_path):
            success_count += 1
            
    console.print(f"\n[bold]Done![/bold] Displayed {success_count}/{len(json_files)} files.")

if __name__ == "__main__":
    main()
