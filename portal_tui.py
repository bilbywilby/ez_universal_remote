#!/data/data/com.termux/files/usr/bin/python3
"""
ez_remote Portal TUI
Interactive IR code lookup with clipboard export and offline support.
"""

from __future__ import annotations

import json
import logging
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.align import Align

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("portal_tui")

console = Console()

@dataclass
class CodeEntry:
    """Single IR code entry."""
    brand: str
    revision: str
    code_length: str  # "3", "4", or "5"
    codes: List[int] = field(default_factory=list)

@dataclass
class TUIState:
    """Application state for persistence."""
    last_search: Optional[str] = None
    search_history: List[str] = field(default_factory=list)
    loaded_at: Optional[str] = None
    total_entries: int = 0
    total_brands: int = 0

class PortalTUI:
    """Terminal User Interface for ez_remote IR code lookup."""
    
    def __init__(self, project_root: Optional[Path] = None) -> None:
        self.project_root = project_root or Path(__file__).parent.parent
        self.data_dir = self.project_root / "remote_intelligence" / "data"
        self.state_path = self.project_root / ".tui_state.json"
        self.codes_map_path = self.data_dir / "codes_map.json"
        
        self.state = TUIState()
        self.code_db: Dict[str, Dict[str, Dict[str, List[int]]]] = {}
        
        self._load_state()
        
        if not self._load_codes_map():
            console.print("[red]❌ Error:[/red] No codes_map.json found. Run the pipeline first.")
            console.print("[yellow]Hint:[/yellow] bash scripts/pipeline_refresh.sh")
            sys.exit(1)
    
    def _load_state(self) -> None:
        """Load persisted TUI state."""
        if self.state_path.exists():
            try:
                with open(self.state_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.state = TUIState(
                    last_search=data.get("last_search"),
                    search_history=data.get("search_history", []),
                    loaded_at=data.get("loaded_at"),
                    total_entries=data.get("total_entries", 0),
                    total_brands=data.get("total_brands", 0)
                )
            except Exception as e:
                logger.warning(f"Failed to load state: {e}")
                self.state = TUIState()
    
    def _save_state(self) -> None:
        """Persist current TUI state."""
        try:
            data = {
                "last_search": self.state.last_search,
                "search_history": self.state.search_history[-20:],  # Keep last 20
                "loaded_at": datetime.now().isoformat(),
                "total_entries": self.state.total_entries,
                "total_brands": self.state.total_brands
            }
            with open(self.state_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save state: {e}")
    
    def _load_codes_map(self) -> bool:
        """Load and validate codes_map.json."""
        if not self.codes_map_path.exists():
            return False
        
        try:
            with open(self.codes_map_path, "r", encoding="utf-8") as f:
                self.code_db = json.load(f)
            
            # Calculate statistics
            total_brands = len(self.code_db)
            total_entries = sum(
                len(revisions) 
                for brand_data in self.code_db.values() 
                for revisions in brand_data.values()
            )
            
            self.state.total_brands = total_brands
            self.state.total_entries = total_entries
            self.state.loaded_at = datetime.now().isoformat()
            
            logger.info(f"Loaded {total_brands} brands, {total_entries} revision entries")
            return True
        except Exception as e:
            console.print(f"[red]❌ Failed to load codes_map.json: {e}[/red]")
            return False
    
    def search_codes(
        self, 
        query: str, 
        search_by: str = "brand"  # "brand", "revision", or "both"
    ) -> List[Tuple[str, str, str, List[int]]]:
        """Search codes by brand name, revision, or both."""
        results = []
        query_lower = query.lower()
        
        for brand, revisions in self.code_db.items():
            brand_match = search_by in ["brand", "both"] and query_lower in brand.lower()
            
            for revision, lengths in revisions.items():
                rev_match = search_by in ["revision", "both"] and query_lower in revision.lower()
                
                if brand_match or rev_match:
                    for length_key, codes in lengths.items():
                        if codes:
                            results.append((brand, revision, length_key, codes))
        
        return results
    
    def copy_to_clipboard(self, text: str) -> bool:
        """Copy text to Termux system clipboard."""
        try:
            proc = subprocess.Popen(
                ["termux-clipboard-set"],
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            proc.communicate(input=text.encode("utf-8"))
            proc.wait(timeout=5)
            return proc.returncode == 0
        except Exception as e:
            logger.error(f"Clipboard failed: {e}")
            return False
    
    def render_brand_table(self, entries: List[Tuple[str, str, str, List[int]]], title: str) -> Table:
        """Render search results in Rich table."""
        table = Table(title=title, expand=True)
        table.add_column("Brand", style="cyan", no_wrap=True)
        table.add_column("Revision", style="magenta", no_wrap=True)
        table.add_column("Code Length", justify="center", style="green")
        table.add_column("Codes", justify="right", style="yellow")
        table.add_column("Count", justify="right", style="dim")
        
        displayed = 0
        for brand, revision, length, codes in entries[:50]:
            codes_str = ", ".join(str(c) for c in codes[:10])
            if len(codes) > 10:
                codes_str += f"... (+{len(codes) - 10})"
            
            table.add_row(
                brand,
                revision,
                f"{length}-digit",
                codes_str,
                str(len(codes))
            )
            displayed += 1
        
        if len(entries) > 50:
            table.caption = f"Showing {displayed} of {len(entries)} results"
        
        return table
    
    def render_statistics(self) -> Panel:
        """Render statistics dashboard panel."""
        brand_list = sorted(self.code_db.keys())
        
        stats_content = []
        stats_content.append(f"[bold blue]Total Brands:[/bold blue] [cyan]{self.state.total_brands}[/cyan]")
        stats_content.append(f"[bold blue]Total Revisions:[/bold blue] [cyan]{self.state.total_entries}[/cyan]")
        
        # Codes by length distribution
        codes_3digit = sum(
            len(lengths.get("3", []))
            for brand_data in self.code_db.values()
            for revisions in brand_data.values()
            for lengths in [revisions]
        )
        codes_4digit = sum(
            len(lengths.get("4", []))
            for brand_data in self.code_db.values()
            for revisions in brand_data.values()
            for lengths in [revisions]
        )
        codes_5digit = sum(
            len(lengths.get("5", []))
            for brand_data in self.code_db.values()
            for revisions in brand_data.values()
            for lengths in [revisions]
        )
        
        stats_content.append(f"\n[cyan]3-digit codes:[/cyan] [yellow]{codes_3digit:,}[/yellow]")
        stats_content.append(f"[cyan]4-digit codes:[/cyan] [yellow]{codes_4digit:,}[/yellow]")
        stats_content.append(f"[cyan]5-digit codes:[/cyan] [yellow]{codes_5digit:,}[/yellow]")
        stats_content.append(f"\n[bold blue]Total IR codes:[/bold blue] [green]{codes_3digit + codes_4digit + codes_5digit:,}[/green]")
        
        # Top 5 brands by code count
        brand_code_counts = []
        for brand, revisions in self.code_db.items():
            total_codes = sum(
                sum(lengths.get(f"{length}", []))
                for revisions_data in revisions.values()
                for lengths in [revisions_data]
                for length in ["3", "4", "5"]
            )
            brand_code_counts.append((brand, total_codes))
        
        brand_code_counts.sort(key=lambda x: x[1], reverse=True)
        if brand_code_counts:
            stats_content.append(f"\n[bold]Top 5 Brands by Code Count:[/bold]")
            for brand, count in brand_code_counts[:5]:
                stats_content.append(f"  • {brand}: [yellow]{count}[/yellow] codes")
        
        stats_content.append(f"\n[dim]Last loaded: {self.state.loaded_at or 'Unknown'}[/dim]")
        
        return Panel(
            "\n".join(stats_content),
            title="[bold]Statistics Dashboard[/bold]",
            border_style="green",
            padding=(1, 2)
        )
    
    def render_main_menu(self) -> str:
        """Render and return main menu choice."""
        console.clear()
        
        header = Text()
        header.append("EZ_REMOTE PORTAL TUI\n", style="bold blue underline")
        header.append(f"{self.state.total_brands} brands • {self.state.total_entries} revisions loaded\n\n", style="dim")
        
        menu_text = Panel(
            header,
            border_style="blue"
        )
        
        console.print(menu_text)
        
        console.print("[bold]Menu:[/]")
        console.print("  [1] Search by brand")
        console.print("  [2] Search by revision")
        console.print("  [3] Browse all brands")
        console.print("  [4] Statistics dashboard")
        console.print("  [5] Export options")
        console.print("  [6] Recent searches")
        console.print("  [0] Exit\n")
        
        return Prompt.ask("[bold cyan]Select option[/bold cyan]", choices=["0", "1", "2", "3", "4", "5", "6"], default="1")
    
    def handle_search_brand(self) -> None:
        """Handle brand search flow."""
        query = Prompt.ask("[cyan]Enter brand name[/cyan]").strip()
        if not query:
            return
        
        self.state.last_search = query
        self.state.search_history.append(query)
        
        results = self.search_codes(query, search_by="brand")
        
        if not results:
            console.print(f"[yellow]No results for '{query}'. Try partial match.[/yellow]")
            return
        
        table = self.render_brand_table(results, f"Results for '{query}'")
        console.print(table)
        
        if results:
            self._offer_export(results, query)
    
    def handle_search_revision(self) -> None:
        """Handle revision search flow."""
        query = Prompt.ask("[cyan]Enter revision (e.g., CL9, Generic)[/cyan]").strip()
        if not query:
            return
        
        self.state.last_search = query
        self.state.search_history.append(query)
        
        results = self.search_codes(query, search_by="revision")
        
        if not results:
            console.print(f"[yellow]No results for revision '{query}'.[/yellow]")
            return
        
        table = self.render_brand_table(results, f"Results for revision '{query}'")
        console.print(table)
        
        if results:
            self._offer_export(results, query)
    
    def handle_browse_all(self) -> None:
        """Browse all available brands alphabetically."""
        table = Table(title="Available Brands")
        table.add_column("Brand", style="cyan")
        table.add_column("Revisions", justify="right", style="magenta")
        table.add_column("Total Codes", justify="right", style="yellow")
        
        sorted_brands = sorted(self.code_db.keys())
        for brand in sorted_brands:
            revisions = self.code_db[brand]
            total_codes = sum(
                sum(lengths.get(f"{length}", []))
                for revisions_data in revisions.values()
                for lengths in [revisions_data]
                for length in ["3", "4", "5"]
            )
            table.add_row(
                brand,
                str(len(revisions)),
                str(total_codes)
            )
        
        console.print(table)
        
        # Pagination prompt for large datasets
        if len(sorted_brands) > 20:
            total_pages = (len(sorted_brands) + 19) // 20
            console.print(f"\n[dim]Showing 20 of {len(sorted_brands)} brands ({total_pages} pages)[/dim]")
    
    def handle_statistics(self) -> None:
        """Display statistics dashboard."""
        console.print(self.render_statistics())
    
    def handle_export(self) -> None:
        """Handle export menu."""
        console.print("[bold]Export Options:[/]")
        console.print("  [1] All codes to CSV")
        console.print("  [2] Last search results to clipboard")
        console.print("  [3] Select brand to export")
        
        choice = Prompt.ask("Select option", choices=["1", "2", "3"], default="1")
        
        if choice == "1":
            self._export_all_to_csv()
        elif choice == "2":
            if not self.state.last_search:
                console.print("[yellow]No previous search to export.[/yellow]")
                return
            self._export_last_search_to_clipboard()
        elif choice == "3":
            self._export_select_brand()
    
    def _export_all_to_csv(self) -> None:
        """Export all codes to CSV file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = self.project_root / f"export_all_{timestamp}.csv"
        
        try:
            lines = ["brand,revision,length,code"]
            
            for brand, revisions in self.code_db.items():
                for revision, lengths in revisions.items():
                    for length, codes in lengths.items():
                        for code in codes:
                            lines.append(f"{brand},{revision},{length},{code}")
            
            output_path.write_text("\n".join(lines), encoding="utf-8")
            console.print(f"[green]✅ Exported to {output_path}[/green]")
            console.print(f"[dim]{len(lines) - 1} codes exported[/dim]")
        except Exception as e:
            console.print(f"[red]❌ Export failed: {e}[/red]")
    
    def _export_last_search_to_clipboard(self) -> None:
        """Export last search results to clipboard."""
        if not self.state.last_search:
            console.print("[yellow]No previous search.[/yellow]")
            return
        
        results = self.search_codes(self.state.last_search, search_by="both")
        if not results:
            console.print("[yellow]No results to export.[/yellow]")
            return
        
        output_text = self._format_results_for_clipboard(results)
        
        if self.copy_to_clipboard(output_text):
            total_codes = sum(len(codes) for _, _, _, codes in results)
            console.print(f"[green]✅ Copied {total_codes} codes to clipboard![/green]")
        else:
            console.print("[yellow]⚠️  Clipboard failed. Here are the codes:[/yellow]")
            console.print(output_text[:1000])  # Show truncated
    
    def _export_select_brand(self) -> None:
        """Allow user to select brand for export."""
        sorted_brands = sorted(self.code_db.keys())
        
        console.print("[bold]Select Brand:[/]")
        for idx, brand in enumerate(sorted_brands[:20], 1):
            console.print(f"  [cyan]{idx}[/cyan]. {brand}")
        
        if len(sorted_brands) > 20:
            console.print(f"  ... and {len(sorted_brands) - 20} more")
        
        try:
            selection = IntPrompt.ask("Enter brand number")
            if 1 <= selection <= len(sorted_brands):
                brand = sorted_brands[selection - 1]
                self._export_single_brand(brand)
        except KeyboardInterrupt:
            console.print("[dim]Cancelled.[/dim]")
    
    def _export_single_brand(self, brand: str) -> None:
        """Export single brand codes to clipboard."""
        results = []
        for revision, lengths in self.code_db.get(brand, {}).items():
            for length, codes in lengths.items():
                if codes:
                    results.append((brand, revision, length, codes))
        
        if not results:
            console.print("[yellow]No codes found for this brand.[/yellow]")
            return
        
        output_text = self._format_results_for_clipboard(results)
        
        if self.copy_to_clipboard(output_text):
            total_codes = sum(len(codes) for _, _, _, codes in results)
            console.print(f"[green]✅ Copied {total_codes} codes for {brand} to clipboard![/green]")
        else:
            console.print("[yellow]Clipboard failed. Codes shown above.[/yellow]")
    
    def _format_results_for_clipboard(self, results: List[Tuple[str, str, str, List[int]]]) -> str:
        """Format results for clipboard (CSV-like format)."""
        lines = ["brand|revision|length|code"]
        for brand, revision, length, codes in results:
            for code in codes:
                lines.append(f"{brand}|{revision}|{length}|{code}")
        return "\n".join(lines)
    
    def _offer_export(self, results: List[Tuple[str, str, str, List[int]]], query: str) -> None:
        """Offer export options after displaying results."""
        if not Confirm.ask("[cyan]Export results to clipboard?[/cyan]", default=False):
            return
        
        output_text = self._format_results_for_clipboard(results)
        total_codes = sum(len(codes) for _, _, _, codes in results)
        
        if self.copy_to_clipboard(output_text):
            console.print(f"[green]✅ Copied {total_codes} codes to clipboard![/green]")
        else:
            console.print("[yellow]⚠️  Clipboard failed. Showing codes below:[/yellow]")
            console.print(output_text[:1000])
    
    def handle_recent_searches(self) -> None:
        """Display and allow reuse of recent searches."""
        if not self.state.search_history:
            console.print("[yellow]No recent searches.[/yellow]")
            return
        
        console.print("[bold]Recent Searches:[/]")
        for idx, search in enumerate(self.state.search_history[-10:], 1):
            console.print(f"  [cyan]{idx}[/cyan]. {search}")
        
        if Confirm.ask("Reuse recent search?", default=False):
            try:
                selection = IntPrompt.ask("Enter number")
                if 1 <= selection <= len(self.state.search_history):
                    query = self.state.search_history[-selection]
                    self.state.last_search = query
                    
                    results = self.search_codes(query, search_by="both")
                    if results:
                        table = self.render_brand_table(results, f"Recent: '{query}'")
                        console.print(table)
                        self._offer_export(results, query)
            except KeyboardInterrupt:
                console.print("[dim]Cancelled.[/dim]")
    
    def run(self) -> None:
        """Main application loop."""
        console.print("[bold green]ez_remote Portal TUI starting...[/bold green]\n")
        
        while True:
            try:
                choice = self.render_main_menu()
                
                if choice == "0":
                    console.print("[yellow]Exiting...[/yellow]")
                    self._save_state()
                    break
                elif choice == "1":
                    self.handle_search_brand()
                elif choice == "2":
                    self.handle_search_revision()
                elif choice == "3":
                    self.handle_browse_all()
                elif choice == "4":
                    self.handle_statistics()
                elif choice == "5":
                    self.handle_export()
                elif choice == "6":
                    self.handle_recent_searches()
                
                if not Confirm.ask("[cyan]Continue?[/cyan]", default=True):
                    console.print("[yellow]Exiting...[/yellow]")
                    self._save_state()
                    break
                
            except KeyboardInterrupt:
                console.print("\n[yellow]Interrupted by user[/yellow]")
                self._save_state()
                break
            except Exception as e:
                console.print(f"[red]❌ Error: {e}[/red]")
                logger.exception("Unhandled exception")
                
                if not Confirm.ask("Continue?", default=True):
                    break


def main() -> None:
    """Entry point for TUI."""
    logger.info("Starting ez_remote Portal TUI")
    
    try:
        tui = PortalTUI()
        tui.run()
    except KeyboardInterrupt:
        logger.info("TUI interrupted by user")
        sys.exit(0)
    except Exception as exc:
        logger.critical(f"TUI crashed: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
