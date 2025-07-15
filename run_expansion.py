import asyncio
import argparse
from dotenv import load_dotenv

from src.services.expansion_service import get_expansion_service

load_dotenv()

async def main():
    """
    Main function to run message expansion as a standalone script.
    """
    parser = argparse.ArgumentParser(description="Run message expansion processing")
    parser.add_argument(
        "--batch-size", 
        type=int, 
        default=1000, 
        help="Number of messages to process in one batch (default: 1000)"
    )
    parser.add_argument(
        "--stats", 
        action="store_true", 
        help="Show expansion statistics only"
    )
    
    args = parser.parse_args()
    
    # Get the expansion service
    service = get_expansion_service()
    
    if args.stats:
        # Show statistics only
        stats = await service.get_expansion_stats()
        print(f"📊 Expansion Statistics:")
        print(f"   Total messages: {stats['total_messages']}")
        print(f"   Expanded messages: {stats['expanded_messages']}")
        print(f"   Pending messages: {stats['pending_messages']}")
        print(f"   Completion: {stats['completion_percentage']:.1f}%")
        return
    
    # Run the expansion process
    print("🚀 Starting message expansion process...")
    
    # Show current stats
    stats = await service.get_expansion_stats()
    print(f"📊 Current stats: {stats['expanded_messages']}/{stats['total_messages']} messages expanded ({stats['completion_percentage']:.1f}%)")
    
    if stats['pending_messages'] > 0:
        print(f"🔄 Processing up to {args.batch_size} messages...")
        processed = await service.process_new_messages(batch_size=args.batch_size)
        print(f"✅ Successfully processed {processed} messages")
    else:
        print("✅ All messages are already expanded")

if __name__ == "__main__":
    asyncio.run(main())