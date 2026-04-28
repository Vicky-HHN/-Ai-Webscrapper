import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from core.scraper import ScraperOrchestrator
import subprocess
import os

app = typer.Typer()
console = Console()

@app.command()
def scrape(prompt: str = typer.Option(..., help="The natural language prompt for scraping")):
    """
    Scrape data based on a natural language prompt.
    """
    orchestrator = ScraperOrchestrator()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task(description="Initializing Scraper...", total=None)

        try:
            result = orchestrator.run(prompt)
            progress.update(task, description="Scraping Complete!")

            if result:
                # Show tips
                interpretation = result.get('interpretation', {})
                suggested = interpretation.get('suggested_fields', [])
                if suggested:
                    console.print(f"\n[bold yellow]Tip:[/bold yellow] You could also extract: {', '.join(suggested)}")

                # Display results table
                records = result['records']
                table = Table(title="Scraped Data Summary")

                if records:
                    for key in records[0].keys():
                        table.add_column(key, style="cyan")

                    for record in records[:5]: # Show first 5 records
                        table.add_row(*[str(v) for v in record.values()])

                console.print(table)
                console.print(f"\n[bold green]Success![/bold green] Saved {len(records)} records.")
                console.print(f"JSON: [blue]{result['json_path']}[/blue]")
                console.print(f"CSV: [blue]{result['csv_path']}[/blue]")
            else:
                console.print("[bold red]No data was scraped.[/bold red]")

        except Exception as e:
            progress.update(task, description="Error!")
            console.print(f"[bold red]Error:[/bold red] {str(e)}")

@app.command()
def dashboard():
    """
    Launch the Streamlit dashboard.
    """
    console.print("[bold green]Launching Streamlit Dashboard...[/bold green]")
    subprocess.run(["streamlit", "run", "app_streamlit.py"])

if __name__ == "__main__":
    app()
