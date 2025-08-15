#!/usr/bin/env python3
"""Flutter Setup CLI - Main entry point."""

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel

from .core import FlutterSetup
from .config import (
    Config,
    FlutterChannel,
    TemplateType,
    IosLanguage,
    AndroidLanguage,
    UpdateMode,
)
from .exceptions import FlutterSetupError

console = Console()


def print_banner() -> None:
    """Print the application banner."""
    banner = """
[bold blue]Flutter Development Environment Setup[/bold blue]
[dim]Automated Flutter development environment setup for macOS[/dim]
    """
    console.print(Panel(banner, border_style="blue"))


@click.command()
@click.argument("project_name", required=True)
@click.argument("platforms", nargs=-1, required=True)
@click.option(
    "--org",
    default="com.example",
    help="Organization identifier (default: com.example)",
)
@click.option(
    "--channel",
    type=click.Choice(["stable", "beta"]),
    default="stable",
    help="Flutter channel (default: stable)",
)
@click.option(
    "--dir",
    default=".",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Output directory (default: current directory)",
)
@click.option(
    "--template",
    type=click.Choice(["app", "plugin"]),
    default="app",
    help="Project template (default: app)",
)
@click.option(
    "--ios-language",
    type=click.Choice(["swift", "objc"]),
    default="swift",
    help="iOS language for plugin templates (default: swift)",
)
@click.option(
    "--android-language",
    type=click.Choice(["kotlin", "java"]),
    default="kotlin",
    help="Android language for plugin templates (default: kotlin)",
)
@click.option(
    "--flutter-update",
    type=click.Choice(["reset", "reclone", "skip"]),
    default="reset",
    help="Flutter update mode (default: reset)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Preview actions without executing them",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose output",
)
def main(
    project_name: str,
    platforms: tuple[str, ...],
    org: str,
    channel: FlutterChannel,
    dir: str,
    template: TemplateType,
    ios_language: IosLanguage,
    android_language: AndroidLanguage,
    flutter_update: UpdateMode,
    dry_run: bool,
    verbose: bool,
) -> None:
    """Set up a complete Flutter development environment."""
    try:
        print_banner()

        # Validate platforms
        if not platforms:
            console.print("[red]Error: At least one platform is required[/red]")
            sys.exit(1)

        # Create configuration
        config = Config(
            project_name=project_name,
            platforms=list(platforms),
            org=org,
            channel=channel,
            output_dir=Path(dir),
            template=template,
            ios_language=ios_language,
            android_language=android_language,
            flutter_update_mode=flutter_update,
            dry_run=dry_run,
            verbose=verbose,
        )

        # Create and run setup
        setup = FlutterSetup(config)
        setup.run()

        console.print("\n[green]✅ Flutter setup completed successfully![/green]")

    except FlutterSetupError as e:
        console.print(f"[red]❌ Setup failed: {e}[/red]")
        if verbose:
            console.print_exception()
        sys.exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  Setup interrupted by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]❌ Unexpected error: {e}[/red]")
        if verbose:
            console.print_exception()
        sys.exit(1)


if __name__ == "__main__":
    # Click handles argument parsing, so we can call main() without arguments
    main()
