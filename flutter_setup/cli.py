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
    Architecture,
    Database,
    Testing,
    AuthProvider,
    CloudDatabase,
    NotificationsProvider,
)
from .config_manager import ConfigManager
from .exceptions import FlutterSetupError
from .prerequisites import PrerequisitesManager
from .flutter_manager import FlutterManager
from .platform import detect_runtime_platform

console = Console()


def print_banner() -> None:
    """Print the application banner."""
    banner = """
[bold blue]Flutter Development Environment Setup[/bold blue]
[dim]Automated Flutter development environment setup for macOS and Linux[/dim]
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

    # Build the config, preserving any existing project settings not covered by init prompts
    existing_project = existing_config.get("project", {}) if existing_config else {}
    config = {
        "flutter": {
            "location": str(flutter_location),
            "channel": channel.lower(),
            "update_mode": (
                existing_config.get("flutter", {}).get("update_mode", "skip")
                if existing_config
                else "skip"
            ),
        },
        "project": {
            "org": org,
            "template": existing_project.get("template", "app"),
            "architecture": existing_project.get("architecture", "basic"),
            "database": existing_project.get("database", "none"),
            "testing": existing_project.get("testing", "standard"),
            "auth_provider": existing_project.get("auth_provider", "none"),
            "cloud_database": existing_project.get("cloud_database", "none"),
            "notifications_provider": existing_project.get(
                "notifications_provider", "none"
            ),
            "ios_language": existing_project.get("ios_language", "swift"),
            "android_language": existing_project.get("android_language", "kotlin"),
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
        host_platform = detect_runtime_platform()
        default_platform = "ios" if host_platform == "darwin" else "linux"

        # Use dummy values for required fields
        config = Config(
            project_name="dummy",
            platforms=[default_platform],
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
@click.argument("project_name", required=False, default=None)
@click.argument("platforms", nargs=-1)
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
    "--architecture",
    type=click.Choice(["basic", "clean"]),
    default="basic",
    help="Application architecture scaffold (default: basic)",
)
@click.option(
    "--database",
    type=click.Choice(["none", "sqlite"]),
    default="none",
    help="Local persistence scaffold (default: none)",
)
@click.option(
    "--testing",
    type=click.Choice(["standard", "mocktail"]),
    default="standard",
    help="Testing starter scaffold (default: standard)",
)
@click.option(
    "--auth-provider",
    type=click.Choice(["none", "firebase"]),
    default="none",
    help="Auth integration scaffold (default: none)",
)
@click.option(
    "--cloud-database",
    type=click.Choice(["none", "firestore"]),
    default="none",
    help="Cloud database integration scaffold (default: none)",
)
@click.option(
    "--notifications-provider",
    type=click.Choice(["none", "firebase"]),
    default="none",
    help="Push notifications scaffold (default: none)",
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
    default="skip",
    help="Flutter update mode (default: skip)",
)
@click.option(
    "--flutter-version",
    default=None,
    help="Required Flutter SDK version (e.g. 3.24.0). Errors early if not installed.",
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
    project_name: str | None,
    platforms: tuple[str, ...],
    org: str,
    channel: FlutterChannel,
    dir: str,
    template: TemplateType,
    architecture: Architecture,
    database: Database,
    testing: Testing,
    auth_provider: AuthProvider,
    cloud_database: CloudDatabase,
    notifications_provider: NotificationsProvider,
    ios_language: IosLanguage,
    android_language: AndroidLanguage,
    flutter_update: UpdateMode,
    flutter_version: str | None,
    dry_run: bool,
    verbose: bool,
) -> None:
    """Set up a complete Flutter development environment."""
    try:
        print_banner()

        # Load configuration from file
        config_manager = ConfigManager()
        config_manager.ensure_config_dir()
        file_config = config_manager.load_config()
        file_project = file_config.get("project", {})
        file_flutter = file_config.get("flutter", {})

        # Get Flutter location from config file
        flutter_location_str = file_config.get("flutter", {}).get("location")
        if flutter_location_str:
            flutter_location = Path(flutter_location_str)
        else:
            flutter_location = Path.home() / "development" / "flutter"
            config_manager.set_flutter_location(flutter_location)

        def get_merged_or_prompt(
            param_name: str,
            cli_value: Any,
            config_dict: Dict[str, Any],
            prompt_text: str,
            choices: list[str] | None = None,
            config_key: str | None = None,
        ) -> Any:
            """Use CLI value if explicit, config file value if present and valid, else prompt."""
            key = config_key or param_name
            if (
                ctx.get_parameter_source(param_name)
                == click.core.ParameterSource.COMMANDLINE
            ):
                return cli_value
            if key in config_dict:
                value = config_dict[key]
                if choices is None or value in choices:
                    return value
                # Config value is invalid — fall through to prompt
            if choices:
                return click.prompt(
                    prompt_text,
                    default=cli_value,
                    type=click.Choice(choices, case_sensitive=False),
                )
            return click.prompt(prompt_text, default=cli_value)

        def get_merged(
            param_name: str,
            cli_value: Any,
            config_dict: Dict[str, Any],
            config_key: str | None = None,
        ) -> Any:
            """Use CLI value if explicit, config file value if present, else CLI default (no prompt)."""
            key = config_key or param_name
            if (
                ctx.get_parameter_source(param_name)
                == click.core.ParameterSource.COMMANDLINE
            ):
                return cli_value
            return config_dict.get(key, cli_value)

        # Prompt for required arguments if not provided on the command line
        if project_name is None:
            project_name = click.prompt("Project name", type=str)

        if not platforms:
            console.print(
                "[dim]Available platforms: ios, android, macos, linux, windows, web[/dim]"
            )
            platforms_str = click.prompt(
                "Platforms (space-separated)",
                default="ios android",
            )
            platforms = tuple(p.strip() for p in platforms_str.split() if p.strip())

        if not platforms:
            console.print("[red]Error: At least one platform is required[/red]")
            sys.exit(1)

        # Merge CLI options with config file, prompting for values not in either
        merged_org = get_merged_or_prompt(
            "org", org, file_project, "Organization ID (e.g., com.mycompany)"
        )
        merged_channel = cast(
            FlutterChannel,
            get_merged_or_prompt(
                "channel",
                channel,
                file_flutter,
                "Flutter channel",
                choices=["stable", "beta"],
            ),
        )
        merged_template = cast(
            TemplateType,
            get_merged_or_prompt(
                "template",
                template,
                file_project,
                "Project template",
                choices=["app", "plugin"],
            ),
        )
        merged_architecture = cast(
            Architecture,
            get_merged_or_prompt(
                "architecture",
                architecture,
                file_project,
                "Architecture",
                choices=["basic", "clean"],
            ),
        )
        merged_database = cast(
            Database,
            get_merged_or_prompt(
                "database",
                database,
                file_project,
                "Local database",
                choices=["none", "sqlite"],
            ),
        )
        merged_testing = cast(
            Testing,
            get_merged_or_prompt(
                "testing",
                testing,
                file_project,
                "Testing framework",
                choices=["standard", "mocktail"],
            ),
        )
        merged_auth_provider = cast(
            AuthProvider,
            get_merged_or_prompt(
                "auth_provider",
                auth_provider,
                file_project,
                "Auth provider",
                choices=["none", "firebase"],
            ),
        )
        merged_cloud_database = cast(
            CloudDatabase,
            get_merged_or_prompt(
                "cloud_database",
                cloud_database,
                file_project,
                "Cloud database",
                choices=["none", "firestore"],
            ),
        )
        merged_notifications_provider = cast(
            NotificationsProvider,
            get_merged_or_prompt(
                "notifications_provider",
                notifications_provider,
                file_project,
                "Notifications provider",
                choices=["none", "firebase"],
            ),
        )
        # Language options only apply to plugin templates; never prompt for app projects
        if merged_template == "plugin":
            merged_ios_language = cast(
                IosLanguage,
                get_merged_or_prompt(
                    "ios_language",
                    ios_language,
                    file_project,
                    "iOS language",
                    choices=["swift", "objc"],
                ),
            )
            merged_android_language = cast(
                AndroidLanguage,
                get_merged_or_prompt(
                    "android_language",
                    android_language,
                    file_project,
                    "Android language",
                    choices=["kotlin", "java"],
                ),
            )
        else:
            merged_ios_language = cast(
                IosLanguage, get_merged("ios_language", ios_language, file_project)
            )
            merged_android_language = cast(
                AndroidLanguage,
                get_merged("android_language", android_language, file_project),
            )
        merged_flutter_update = cast(
            UpdateMode,
            get_merged_or_prompt(
                "flutter_update",
                flutter_update,
                file_flutter,
                "Flutter update mode",
                choices=["reset", "reclone", "skip"],
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
            architecture=merged_architecture,
            database=merged_database,
            testing=merged_testing,
            auth_provider=merged_auth_provider,
            cloud_database=merged_cloud_database,
            notifications_provider=merged_notifications_provider,
            flutter_version=flutter_version,
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
