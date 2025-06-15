"""CLI commands for deduplication management.

This module provides command-line interface commands for managing document duplicates
in the Biblioperson deduplication system.

Author: Biblioperson
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

try:
    from tabulate import tabulate
except ImportError:
    tabulate = None

# Import deduplication components
try:
    from .deduplication import get_dedup_manager
    from .dedup_config import get_config_manager
except ImportError:
    # Fallback for direct execution
    import sys
    sys.path.append(str(Path(__file__).parent))
    from deduplication import get_dedup_manager
    from dedup_config import get_config_manager

logger = logging.getLogger("biblioperson.dedup_cli")

# --------------------------------------------------------------------------- #
#                                   Helpers                                   #
# --------------------------------------------------------------------------- #

def format_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def format_date(date_str: str) -> str:
    """Format ISO date string for display."""
    try:
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M')
    except (ValueError, AttributeError):
        return date_str

def truncate_text(text: str, max_length: int = 50) -> str:
    """Truncate text to specified length with ellipsis."""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

def print_table(data: List[Dict[str, Any]], headers: List[str], format_type: str = "ascii") -> None:
    """Print data in table format."""
    if not data:
        print("No data to display.")
        return
    
    if format_type == "json":
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return
    
    if tabulate is None:
        # Fallback to simple formatting if tabulate not available
        print("\t".join(headers))
        print("-" * 80)
        for row in data:
            values = [str(row.get(h.lower().replace(' ', '_'), '')) for h in headers]
            print("\t".join(values))
        return
    
    # Use tabulate for nice formatting
    table_data = []
    for row in data:
        table_row = []
        for header in headers:
            key = header.lower().replace(' ', '_')
            value = row.get(key, '')
            
            # Special formatting for specific columns
            if 'size' in key and isinstance(value, (int, float)):
                value = format_size(int(value))
            elif 'date' in key or 'seen' in key:
                value = format_date(str(value))
            elif 'hash' in key:
                value = truncate_text(str(value), 12)
            elif 'path' in key:
                value = truncate_text(str(value), 40)
            elif 'title' in key:
                value = truncate_text(str(value), 30)
            
            table_row.append(value)
        table_data.append(table_row)
    
    print(tabulate(table_data, headers=headers, tablefmt="grid"))

def confirm_action(message: str, force: bool = False) -> bool:
    """Ask for confirmation unless force is True."""
    if force:
        return True
    
    response = input(f"{message} (y/N): ").strip().lower()
    return response in ('y', 'yes')

# --------------------------------------------------------------------------- #
#                              Command Functions                              #
# --------------------------------------------------------------------------- #

def cmd_list(args: argparse.Namespace) -> int:
    """List documents with optional filters."""
    try:
        dedup_manager = get_dedup_manager()
        
        # Apply filters
        documents = dedup_manager.list_documents(
            search=args.search,
            before=args.before,
            after=args.after
        )
        
        if not documents:
            print("No documents found matching the criteria.")
            return 0
        
        # Apply limit and offset
        total = len(documents)
        start = args.offset
        end = start + args.limit if args.limit else len(documents)
        documents = documents[start:end]
        
        if args.format == "json":
            result = {
                "documents": documents,
                "total": total,
                "showing": len(documents),
                "offset": args.offset
            }
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            headers = ["Hash", "Title", "File Path", "First Seen", "Size"]
            print_table(documents, headers, args.format)
            
            if total > len(documents):
                print(f"\nShowing {len(documents)} of {total} documents (offset: {args.offset})")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        return 1

def cmd_remove(args: argparse.Namespace) -> int:
    """Remove documents by hash, path, or search pattern."""
    try:
        dedup_manager = get_dedup_manager()
        
        removed_count = 0
        
        if args.hash:
            # Remove by hash
            if confirm_action(f"Remove document with hash {args.hash[:12]}...?", args.force):
                if dedup_manager.remove_by_hash(args.hash):
                    print(f"Document with hash {args.hash[:12]}... removed successfully.")
                    removed_count = 1
                else:
                    print(f"Document with hash {args.hash[:12]}... not found.")
                    return 1
        
        elif args.path:
            # Remove by path
            if confirm_action(f"Remove document at path '{args.path}'?", args.force):
                if dedup_manager.remove_by_path(args.path):
                    print(f"Document at '{args.path}' removed successfully.")
                    removed_count = 1
                else:
                    print(f"Document at '{args.path}' not found.")
                    return 1
        
        elif args.search:
            # Remove by search pattern
            documents = dedup_manager.list_documents(search=args.search)
            if not documents:
                print(f"No documents found matching search '{args.search}'.")
                return 0
            
            print(f"Found {len(documents)} documents matching '{args.search}':")
            headers = ["Hash", "Title", "File Path"]
            print_table(documents, headers)
            
            if confirm_action(f"Remove all {len(documents)} documents?", args.force):
                for doc in documents:
                    if dedup_manager.remove_by_hash(doc['hash']):
                        removed_count += 1
                
                print(f"Removed {removed_count} documents successfully.")
        
        else:
            print("Error: Must specify --hash, --path, or --search")
            return 1
        
        return 0
        
    except Exception as e:
        logger.error(f"Error removing documents: {e}")
        return 1

def cmd_prune(args: argparse.Namespace) -> int:
    """Remove documents before a specific date."""
    try:
        dedup_manager = get_dedup_manager()
        
        # First, show what would be removed
        documents = dedup_manager.list_documents(before=args.before)
        if not documents:
            print(f"No documents found before {args.before}.")
            return 0
        
        print(f"Found {len(documents)} documents before {args.before}:")
        if not args.quiet:
            headers = ["Hash", "Title", "First Seen"]
            print_table(documents[:10], headers)  # Show first 10
            if len(documents) > 10:
                print(f"... and {len(documents) - 10} more documents")
        
        if confirm_action(f"Remove all {len(documents)} documents before {args.before}?", args.force):
            removed_count = 0
            for doc in documents:
                if dedup_manager.remove_by_hash(doc['hash']):
                    removed_count += 1
            
            print(f"Removed {removed_count} documents successfully.")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error pruning documents: {e}")
        return 1

def cmd_clear(args: argparse.Namespace) -> int:
    """Remove all documents from the deduplication database."""
    try:
        dedup_manager = get_dedup_manager()
        
        # Get current stats
        stats = dedup_manager.get_stats()
        total_docs = stats.get('total_documents', 0)
        
        if total_docs == 0:
            print("No documents to clear.")
            return 0
        
        print(f"This will remove ALL {total_docs} documents from the deduplication database.")
        print("This action cannot be undone!")
        
        if confirm_action("Are you sure you want to clear all documents?", args.force):
            cleared_count = dedup_manager.clear_all()
            if cleared_count >= 0:
                print(f"Successfully cleared {cleared_count} documents from the database.")
            else:
                print("Failed to clear the database.")
                return 1
        
        return 0
        
    except Exception as e:
        logger.error(f"Error clearing database: {e}")
        return 1

def cmd_stats(args: argparse.Namespace) -> int:
    """Show deduplication database statistics."""
    try:
        dedup_manager = get_dedup_manager()
        stats = dedup_manager.get_stats()
        
        if args.format == "json":
            print(json.dumps(stats, indent=2, ensure_ascii=False))
        else:
            print("Deduplication Database Statistics")
            print("=" * 40)
            print(f"Total documents: {stats.get('total_documents', 0)}")
            print(f"Total size: {format_size(stats.get('total_size_bytes', 0))}")
            print(f"Average file size: {format_size(stats.get('average_file_size', 0))}")
            print(f"Database size: {format_size(stats.get('database_size_bytes', 0))}")
            
            if stats.get('oldest_document'):
                print(f"Oldest document: {format_date(stats['oldest_document'])}")
            if stats.get('newest_document'):
                print(f"Newest document: {format_date(stats['newest_document'])}")
            
            print(f"Documents today: {stats.get('documents_today', 0)}")
            print(f"Documents this week: {stats.get('documents_this_week', 0)}")
            print(f"Documents this month: {stats.get('documents_this_month', 0)}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        return 1

def cmd_config(args: argparse.Namespace) -> int:
    """Show deduplication configuration."""
    try:
        config_manager = get_config_manager()
        
        if args.format == "json":
            config_data = {
                "deduplication_enabled": config_manager.is_deduplication_enabled(),
                "database_path": str(config_manager.get_database_path()),
                "config": config_manager.get_deduplication_config().__dict__
            }
            print(json.dumps(config_data, indent=2, ensure_ascii=False))
        else:
            print("Deduplication Configuration")
            print("=" * 40)
            print(f"Enabled: {config_manager.is_deduplication_enabled()}")
            print(f"Database path: {config_manager.get_database_path()}")
            
            config = config_manager.get_deduplication_config()
            print(f"Default output mode: {config.default_output_mode}")
            print(f"Continue on error: {config.continue_on_error}")
            print(f"Log errors: {config.log_errors}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error getting configuration: {e}")
        return 1

# --------------------------------------------------------------------------- #
#                              Argument Parser                                #
# --------------------------------------------------------------------------- #

def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser for deduplication CLI."""
    parser = argparse.ArgumentParser(
        prog="dedup",
        description="Manage document deduplication database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  dedup list                              # List all documents
  dedup list --search "novela"            # Search for documents
  dedup list --before 2025-01-01          # Documents before date
  dedup list --format json               # Output as JSON
  
  dedup remove --hash abc123...           # Remove by hash
  dedup remove --path "/docs/file.pdf"    # Remove by path
  dedup remove --search "test" --force    # Remove by search (no confirmation)
  
  dedup prune --before 2025-01-01        # Remove old documents
  dedup clear --force                     # Clear all documents
  
  dedup stats                             # Show statistics
  dedup config                            # Show configuration
        """
    )
    
    # Global options
    parser.add_argument(
        "--format", 
        choices=["ascii", "json"], 
        default="ascii",
        help="Output format (default: ascii)"
    )
    parser.add_argument(
        "--verbose", "-v", 
        action="store_true",
        help="Enable verbose output"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List documents")
    list_parser.add_argument("--search", help="Search in title or file path")
    list_parser.add_argument("--before", help="Documents before date (YYYY-MM-DD)")
    list_parser.add_argument("--after", help="Documents after date (YYYY-MM-DD)")
    list_parser.add_argument("--limit", type=int, help="Maximum number of results")
    list_parser.add_argument("--offset", type=int, default=0, help="Number of results to skip")
    list_parser.add_argument("--format", choices=["ascii", "json"], default="ascii", help="Output format")
    
    # Remove command
    remove_parser = subparsers.add_parser("remove", help="Remove documents")
    remove_group = remove_parser.add_mutually_exclusive_group(required=True)
    remove_group.add_argument("--hash", help="Remove document by hash")
    remove_group.add_argument("--path", help="Remove document by file path")
    remove_group.add_argument("--search", help="Remove documents matching search")
    remove_parser.add_argument("--force", action="store_true", help="Skip confirmation")
    
    # Prune command
    prune_parser = subparsers.add_parser("prune", help="Remove documents before date")
    prune_parser.add_argument("--before", required=True, help="Remove documents before date (YYYY-MM-DD)")
    prune_parser.add_argument("--force", action="store_true", help="Skip confirmation")
    prune_parser.add_argument("--quiet", action="store_true", help="Don't show document list")
    
    # Clear command
    clear_parser = subparsers.add_parser("clear", help="Remove all documents")
    clear_parser.add_argument("--force", action="store_true", help="Skip confirmation")
    
    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show database statistics")
    stats_parser.add_argument("--format", choices=["ascii", "json"], default="ascii", help="Output format")
    
    # Config command
    config_parser = subparsers.add_parser("config", help="Show configuration")
    config_parser.add_argument("--format", choices=["ascii", "json"], default="ascii", help="Output format")
    
    return parser

# --------------------------------------------------------------------------- #
#                                Main Function                                #
# --------------------------------------------------------------------------- #

def main(argv: Optional[List[str]] = None) -> int:
    """Main entry point for deduplication CLI."""
    parser = create_parser()
    args = parser.parse_args(argv)
    
    # Set up logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(levelname)s - %(message)s"
    )
    
    # Check if deduplication is available
    try:
        config_manager = get_config_manager()
        if not config_manager.is_deduplication_enabled():
            print("Warning: Deduplication is disabled in configuration.")
            if args.command not in ['config']:
                return 1
    except Exception as e:
        logger.error(f"Error accessing deduplication system: {e}")
        return 1
    
    # Route to appropriate command
    if args.command == "list":
        return cmd_list(args)
    elif args.command == "remove":
        return cmd_remove(args)
    elif args.command == "prune":
        return cmd_prune(args)
    elif args.command == "clear":
        return cmd_clear(args)
    elif args.command == "stats":
        return cmd_stats(args)
    elif args.command == "config":
        return cmd_config(args)
    else:
        parser.print_help()
        return 1

if __name__ == "__main__":
    sys.exit(main())