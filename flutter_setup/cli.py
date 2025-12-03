#!/usr/bin/env python3
"""Flutter Setup CLI - Main entry point."""

import sys
from pathlib import Path
from typing import Any, Dict, cast

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
from .config_manager import ConfigManager
from .exceptions import FlutterSetupError
from .prerequisites import PrerequisitesManager
from .flutter_manager import FlutterManager

console = Console()


def merge_cli_with_config(
    ctx: click.Context,
    param_name: str,
    cli_value: Any,
    file_config: Dict[str, Any],
    config_key: str | None = None,
) -> Any:
    """
    Merge CLI parameter with config file value.

    If the parameter was explicitly provided via command line, use the CLI value.
    Otherwise, use the config file value if available, or fall back to CLI value.

    Args:
        ctx: Click context to check parameter source
        param_name: Name of the CLI parameter
        cli_value: Value from CLI (may be default)
        file_config: Dictionary from config file to look up values
        config_key: Key name in config file (defaults to param_name)

    Returns:
        Merged value (CLI value if explicitly provided, else config file value or CLI default)
    """
    config_key = config_key or param_name
    if ctx.get_parameter_source(param_name) == click.core.ParameterSource.COMMANDLINE:
        return cli_value
    return file_config.get(config_key, cli_value)


def print_banner() -> None:
    """Print the application banner."""
    banner = """
[bold blue]Flutter Development Environment Setup[/bold blue]
[dim]Automated Flutter development environment setup for macOS[/dim]
    """
    console.print(Panel(banner, border_style="blue"))


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx: click.Context) -> None:
    """Flutter Development Environment Setup CLI."""
    # If no subcommand provided, show banner and help
    if ctx.invoked_subcommand is None:
        print_banner()
        click.echo(ctx.get_help())


@cli.command("init")
@click.option(
    "--force",
    is_flag=True,
    help="Overwrite existing config file if it exists",
)
def init_config(force: bool) -> None:
    """Initialize the configuration file interactively."""
    config_manager = ConfigManager()
    config_manager.ensure_config_dir()

    # Load existing config if it exists
    existing_config = None
    if config_manager.config_file.exists():
        if not force:
            console.print(
                f"[yellow]⚠️  Config file already exists at: {config_manager.config_file}[/yellow]"
            )
            console.print("[dim]Loading existing configuration for editing...[/dim]\n")
        existing_config = config_manager.load_config()

    # Start interactive configuration
    console.print("[bold blue]Flutter Setup Configuration[/bold blue]\n")

    # 1. Flutter Location
    console.print("[bold]1. Flutter SDK Location[/bold]")
    if existing_config:
        current_location = existing_config.get("flutter", {}).get("location", "")
        console.print(f"[dim]Current: {current_location}[/dim]")
    else:
        # Try to detect Flutter location
        detected = config_manager.detect_flutter_location()
        if detected:
            console.print(f"[green]✓ Detected Flutter at: {detected}[/green]")
            current_location = str(detected)
        else:
            default_location = str(Path.home() / "development" / "flutter")
            console.print(f"[dim]Default: {default_location}[/dim]")
            current_location = default_location

    flutter_location_input = click.prompt(
        "Flutter location",
        default=current_location,
        type=str,
    )
    flutter_location = Path(flutter_location_input).expanduser().resolve()

    # Validate Flutter location
    if not flutter_location.exists():
        console.print(
            "[yellow]⚠️  Warning: Path does not exist. It will be created when Flutter is installed.[/yellow]"
        )

    # 2. Flutter Channel
    console.print("\n[bold]2. Flutter Channel[/bold]")
    if existing_config:
        current_channel = existing_config.get("flutter", {}).get("channel", "stable")
        console.print(f"[dim]Current: {current_channel}[/dim]")
    else:
        current_channel = "stable"

    channel = click.prompt(
        "Flutter channel",
        default=current_channel,
        type=click.Choice(["stable", "beta"], case_sensitive=False),
    )

    # 3. Organization ID
    console.print("\n[bold]3. Organization ID[/bold]")
    if existing_config:
        current_org = existing_config.get("project", {}).get("org", "com.example")
        console.print(f"[dim]Current: {current_org}[/dim]")
    else:
        current_org = "com.example"

    org = click.prompt(
        "Organization ID (e.g., com.example, com.mycompany)",
        default=current_org,
        type=str,
    )

    # Build the config
    config = {
        "flutter": {
            "location": str(flutter_location),
            "channel": channel.lower(),
            "update_mode": (
                existing_config.get("flutter", {}).get("update_mode", "reset")
                if existing_config
                else "reset"
            ),
        },
        "project": {
            "org": org,
            "template": (
                existing_config.get("project", {}).get("template", "app")
                if existing_config
                else "app"
            ),
            "ios_language": (
                existing_config.get("project", {}).get("ios_language", "swift")
                if existing_config
                else "swift"
            ),
            "android_language": (
                existing_config.get("project", {}).get("android_language", "kotlin")
                if existing_config
                else "kotlin"
            ),
        },
    }

    # Save the config
    config_manager.save_config(config)

    # Show summary
    console.print("\n[green]✅ Configuration saved![/green]")
    console.print("\n[bold]Config file location:[/bold]")
    console.print(f"  {config_manager.config_file}")
    console.print("\n[bold]Configuration summary:[/bold]")
    console.print(f"  Flutter location: {config['flutter']['location']}")
    console.print(f"  Flutter channel: {config['flutter']['channel']}")
    console.print(f"  Organization: {config['project']['org']}")
    console.print(
        "\n[dim]You can edit this file directly or run 'flutter-setup init' again to update it.[/dim]"
    )


@cli.command("check")
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose output",
)
def check_command(verbose: bool) -> None:
    """Check that prerequisites and Flutter SDK are ready and updated."""
    try:
        print_banner()
        console.print("\n[bold]🔍 Checking Flutter development environment...[/bold]\n")

        # Load configuration from file
        config_manager = ConfigManager()
        config_manager.ensure_config_dir()
        file_config = config_manager.load_config()

        # Get Flutter location from config file
        flutter_location_str = file_config.get("flutter", {}).get("location")
        if flutter_location_str:
            flutter_location = Path(flutter_location_str)
        else:
            # Fallback to default if not in config
            flutter_location = Path.home() / "development" / "flutter"

        # Get channel from config
        channel = file_config.get("flutter", {}).get("channel", "stable")

        # Create minimal config for checking (we don't need project details)
        # Use dummy values for required fields
        config = Config(
            project_name="dummy",
            platforms=["ios"],  # Default platform for checks
            org="com.example",
            channel=channel,
            output_dir=Path("."),
            template="app",
            ios_language="swift",
            android_language="kotlin",
            flutter_update_mode="skip",  # Don't update during check
            dry_run=False,
            verbose=verbose,
            flutter_location=flutter_location,
        )

        # Check prerequisites
        console.print("[bold]📋 Checking prerequisites...[/bold]")
        prerequisites = PrerequisitesManager(config)
        prerequisites_ok = prerequisites.check_only()

        # Check Flutter SDK
        console.print("\n[bold]🦋 Checking Flutter SDK...[/bold]")
        flutter_manager = FlutterManager(config)
        flutter_ok = flutter_manager.check_only()

        # Summary
        console.print("\n[bold]📊 Summary[/bold]")
        if prerequisites_ok and flutter_ok:
            console.print(
                "[green]✅ All checks passed! Your Flutter development environment is ready.[/green]"
            )
            sys.exit(0)
        else:
            console.print(
                "[yellow]⚠️  Some checks failed. Please review the issues above.[/yellow]"
            )
            if not prerequisites_ok:
                console.print(
                    "[dim]Run 'flutter-setup setup <project> <platforms>' to install missing prerequisites.[/dim]"
                )
            if not flutter_ok:
                console.print(
                    "[dim]Run 'flutter-setup setup <project> <platforms>' to install or update Flutter SDK.[/dim]"
                )
            sys.exit(1)

    except Exception as e:
        console.print(f"[red]❌ Check failed: {e}[/red]")
        if verbose:
            console.print_exception()
        sys.exit(1)


@cli.command("setup")
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
@click.pass_context
def setup_command(
    ctx: click.Context,
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

        # Load configuration from file
        config_manager = ConfigManager()
        config_manager.ensure_config_dir()
        file_config = config_manager.load_config()

        # Get Flutter location from config file
        flutter_location_str = file_config.get("flutter", {}).get("location")
        if flutter_location_str:
            flutter_location = Path(flutter_location_str)
        else:
            # Fallback to default if not in config
            flutter_location = Path.home() / "development" / "flutter"
            # Save default to config file
            config_manager.set_flutter_location(flutter_location)

        # Merge file config with command-line arguments
        # CLI args always take precedence when explicitly provided
        file_project = file_config.get("project", {})
        file_flutter = file_config.get("flutter", {})

        # Check parameter sources to determine if CLI values were explicitly provided
        # If provided via command line, always use CLI value (even if it matches default)
        # Otherwise, use file config value if available, or fall back to CLI value (default)
        # For each option: use CLI value if explicitly provided, otherwise use file config
        merged_org = merge_cli_with_config(ctx, "org", org, file_project)
        merged_channel = cast(
            FlutterChannel,
            merge_cli_with_config(ctx, "channel", channel, file_flutter),
        )
        merged_template = cast(
            TemplateType,
            merge_cli_with_config(ctx, "template", template, file_project),
        )
        merged_ios_language = cast(
            IosLanguage,
            merge_cli_with_config(ctx, "ios_language", ios_language, file_project),
        )
        merged_android_language = cast(
            AndroidLanguage,
            merge_cli_with_config(
                ctx, "android_language", android_language, file_project
            ),
        )
        merged_flutter_update = cast(
            UpdateMode,
            merge_cli_with_config(
                ctx,
                "flutter_update",
                flutter_update,
                file_flutter,
                config_key="update_mode",
            ),
        )

        # Create configuration
        config = Config(
            project_name=project_name,
            platforms=list(platforms),
            org=merged_org,
            channel=merged_channel,
            output_dir=Path(dir),
            template=merged_template,
            ios_language=merged_ios_language,
            android_language=merged_android_language,
            flutter_update_mode=merged_flutter_update,
            dry_run=dry_run,
            verbose=verbose,
            flutter_location=flutter_location,
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


def main() -> None:
    """Main entry point that routes to appropriate command."""
    cli()


if __name__ == "__main__":
    # Click handles argument parsing
    main()
