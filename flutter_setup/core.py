"""Core Flutter setup functionality."""

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel

from .config import Config
from .exceptions import (
    FlutterSetupError,
    PrerequisitesError,
    FlutterInstallationError,
    ProjectCreationError,
)
from .prerequisites import PrerequisitesManager
from .flutter_manager import FlutterManager
from .project_creator import ProjectCreator
from .bootstrap import ProjectBootstrap

console = Console()


class FlutterSetup:
    """Main class for orchestrating Flutter development environment setup."""

    def __init__(self, config: Config):
        """Initialize FlutterSetup with configuration."""
        self.config = config
        self.prerequisites = PrerequisitesManager(config)
        self.flutter_manager = FlutterManager(config)
        self.project_creator = ProjectCreator(config)
        self.bootstrap = ProjectBootstrap(config)

    def run(self) -> None:
        """Run the complete Flutter setup process."""
        console.print(
            f"\n[bold blue]🚀 Starting Flutter setup for: {self.config.project_name}[/bold blue]"
        )
        console.print(
            f"[dim]Template: {self.config.template} | Org: {self.config.org} | Channel: {self.config.channel}[/dim]"
        )
        console.print(
            f"[dim]Platforms: {', '.join(self.config.platforms)} | Package: {self.config.package_name}[/dim]"
        )
        console.print(f"[dim]Output: {self.config.project_path}[/dim]")

        if self.config.dry_run:
            console.print(
                "[yellow]⚠️  DRY RUN MODE - No actual changes will be made[/yellow]"
            )

        try:
            # Step 1: Check and install prerequisites
            self._run_prerequisites()

            # Step 2: Install/update Flutter SDK
            self._run_flutter_installation()

            # Step 3: Create Flutter project
            self._run_project_creation()

            # Step 4: Bootstrap development environment
            self._run_bootstrap()

            # Step 5: Display next steps
            self._show_next_steps()

        except Exception as e:
            console.print(f"\n[red]❌ Setup failed: {e}[/red]")
            raise

    def _run_prerequisites(self) -> None:
        """Run prerequisites check and installation."""
        console.print("\n[bold]📋 Checking prerequisites...[/bold]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Checking system requirements...", total=None)

            try:
                self.prerequisites.check_and_install()
                progress.update(task, description="✅ Prerequisites satisfied")
            except Exception as e:
                progress.update(task, description="❌ Prerequisites failed")
                raise PrerequisitesError(f"Failed to install prerequisites: {e}")

    def _run_flutter_installation(self) -> None:
        """Run Flutter SDK installation/update."""
        console.print("\n[bold]🦋 Installing/updating Flutter SDK...[/bold]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Setting up Flutter SDK...", total=None)

            try:
                self.flutter_manager.ensure_flutter()
                progress.update(task, description="✅ Flutter SDK ready")
            except Exception as e:
                progress.update(task, description="❌ Flutter installation failed")
                raise FlutterInstallationError(f"Failed to install Flutter: {e}")

    def _run_project_creation(self) -> None:
        """Run Flutter project creation."""
        console.print("\n[bold]🏗️  Creating Flutter project...[/bold]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Creating project structure...", total=None)

            try:
                self.project_creator.create_project()
                progress.update(task, description="✅ Project created")
            except Exception as e:
                progress.update(task, description="❌ Project creation failed")
                raise ProjectCreationError(f"Failed to create project: {e}")

    def _run_bootstrap(self) -> None:
        """Run project bootstrapping."""
        console.print("\n[bold]🔧 Bootstrapping development environment...[/bold]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Setting up development tools...", total=None)

            try:
                self.bootstrap.bootstrap_project()
                progress.update(task, description="✅ Development environment ready")
            except Exception as e:
                progress.update(task, description="❌ Bootstrap failed")
                raise FlutterSetupError(f"Failed to bootstrap project: {e}")

    def _show_next_steps(self) -> None:
        """Display next steps for the user."""
        console.print("\n[bold green]🎉 Setup completed successfully![/bold green]")

        next_steps = f"""
[bold]Next steps:[/bold]

1. [blue]Activate Flutter in your shell:[/blue]
   [code]source ~/.zprofile[/code]

2. [blue]Navigate to your project:[/blue]
   [code]cd "{self.config.project_path}"[/code]

3. [blue]Run your Flutter app:[/blue]
   [code]make run[/code]           # runs on Chrome by default
   [code]make run_ios[/code]       # runs on iOS simulator
   [code]make run_android[/code]   # runs on Android emulator

4. [blue]Test your setup:[/blue]
   [code]make test[/code]          # run unit + widget tests
   [code]make analyze[/code]       # check lints

5. [blue]Open in Cursor/VS Code:[/blue]
   Hit F5 ("Flutter Debug") to start debugging

[dim]Your project is located at: {self.config.project_path}[/dim]
        """

        console.print(
            Panel(next_steps, title="🚀 Ready to Code!", border_style="green")
        )
