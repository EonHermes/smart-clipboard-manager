#!/usr/bin/env python3
"""Smart Clipboard Manager - CLI Entry Point."""

import argparse
import sys
from datetime import datetime

from .utils.config import get_config
from .clipboard.storage import ClipStorage
from .clipboard.monitor import ClipboardMonitor


def cmd_list(args):
    """List recent clips."""
    storage = ClipStorage()
    clips = storage.get_recent(limit=args.limit)
    
    if not clips:
        print("No clips found.")
        return
    
    print(f"\n{'='*60}")
    print(f"Recent Clips ({len(clips)} shown)")
    print(f"{'='*60}\n")
    
    for i, clip in enumerate(clips, 1):
        preview = clip.content[:80] + "..." if len(clip.content) > 80 else clip.content
        print(f"{i}. [{clip.clip_type.upper()}] {preview}")
        print(f"   ID: {clip.id} | Created: {clip.created_at.strftime('%Y-%m-%d %H:%M')}")
        if clip.category:
            print(f"   Category: {clip.category}")
        print()


def cmd_search(args):
    """Search clips."""
    storage = ClipStorage()
    clips = storage.search(query=args.query, limit=args.limit)
    
    if not clips:
        print("No matching clips found.")
        return
    
    print(f"\n{'='*60}")
    print(f"Search Results for '{args.query}' ({len(clips)} found)")
    print(f"{'='*60}\n")
    
    for i, clip in enumerate(clips, 1):
        preview = clip.content[:80] + "..." if len(clip.content) > 80 else clip.content
        print(f"{i}. [{clip.clip_type.upper()}] {preview}")
        print(f"   ID: {clip.id} | Category: {clip.category or 'N/A'}")
        print()


def cmd_capture(args):
    """Manually capture clipboard."""
    storage = ClipStorage()
    monitor = ClipboardMonitor(storage)
    
    result = monitor.capture_now()
    
    if result:
        print(f"✓ Captured clip #{result['id']}")
        print(f"  Type: {result['clip_type']}")
        print(f"  Preview: {result['content'][:100]}...")
    else:
        print("No content in clipboard.")


def cmd_monitor(args):
    """Start background monitoring."""
    storage = ClipStorage()
    monitor = ClipboardMonitor(storage)
    
    def on_capture(content, clip_type):
        preview = content[:50] + "..." if len(content) > 50 else content
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Captured {clip_type}: {preview}")
    
    monitor.add_callback(on_capture)
    
    print("Starting clipboard monitor (Ctrl+C to stop)...")
    monitor.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping...")
        monitor.stop()


def cmd_stats(args):
    """Show storage statistics."""
    storage = ClipStorage()
    stats = storage.get_stats()
    
    print(f"\n{'='*60}")
    print("Clipboard Statistics")
    print(f"{'='*60}\n")
    print(f"Total clips: {stats['total_clips']}")
    print("\nBy type:")
    for clip_type, count in stats['by_type'].items():
        print(f"  - {clip_type}: {count}")
    print()


def cmd_categorize(args):
    """Manually categorize a clip."""
    storage = ClipStorage()
    
    if storage.update_category(args.id, args.category):
        print(f"✓ Clip #{args.id} categorized as '{args.category}'")
    else:
        print(f"✗ Clip #{args.id} not found.")


def cmd_export(args):
    """Export clips to file."""
    storage = ClipStorage()
    clips = storage.get_recent(limit=args.limit)
    
    import json
    
    data = {
        "exported_at": datetime.now().isoformat(),
        "total_clips": len(clips),
        "clips": [clip.to_dict() for clip in clips]
    }
    
    with open(args.output, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"✓ Exported {len(clips)} clips to {args.output}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Smart Clipboard Manager - AI-powered clipboard management",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s list --limit 10       # Show recent clips
  %(prog)s search "python code"  # Search clips
  %(prog)s capture               # Manually capture clipboard
  %(prog)s monitor               # Start background monitoring
  %(prog)s stats                 # Show statistics
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List recent clips")
    list_parser.add_argument("--limit", "-n", type=int, default=10, help="Number of clips to show")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search clips")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--limit", "-n", type=int, default=10, help="Max results")
    
    # Capture command
    subparsers.add_parser("capture", help="Manually capture clipboard")
    
    # Monitor command
    monitor_parser = subparsers.add_parser("monitor", help="Start background monitoring")
    
    # Stats command
    subparsers.add_parser("stats", help="Show statistics")
    
    # Categorize command
    cat_parser = subparsers.add_parser("categorize", help="Categorize a clip")
    cat_parser.add_argument("--id", type=int, required=True, help="Clip ID")
    cat_parser.add_argument("--category", "-c", required=True, help="Category name")
    
    # Export command
    export_parser = subparsers.add_parser("export", help="Export clips")
    export_parser.add_argument("--output", "-o", required=True, help="Output file path")
    export_parser.add_argument("--limit", "-n", type=int, default=100, help="Max clips to export")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(0)
    
    # Import time for monitor command
    if args.command == "monitor":
        import time
    
    commands = {
        "list": cmd_list,
        "search": cmd_search,
        "capture": cmd_capture,
        "monitor": cmd_monitor,
        "stats": cmd_stats,
        "categorize": cmd_categorize,
        "export": cmd_export,
    }
    
    if args.command in commands:
        try:
            commands[args.command](args)
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
