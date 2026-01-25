"""Download and setup Chinook sample database for testing.

Chinook is a sample database representing a digital media store with:
- Artists, Albums, Tracks (3,500+ tracks)
- Customers, Invoices, Sales data
- Employees, Playlists, Genres
- 11 tables with realistic foreign key relationships

More interesting than stub TPC-H data for testing agent capabilities.

Source: https://github.com/lerocha/chinook-database
"""

import sqlite3
import urllib.request
from pathlib import Path

# Chinook SQLite database direct download
CHINOOK_URL = "https://github.com/lerocha/chinook-database/raw/master/ChinookDatabase/DataSources/Chinook_Sqlite.sqlite"


def download_chinook_db(output_path: Path) -> None:
    """Download Chinook database from GitHub.

    Args:
        output_path: Path where database will be saved
    """
    print(f"Downloading Chinook database from: {CHINOOK_URL}")
    print(f"Saving to: {output_path}")

    try:
        urllib.request.urlretrieve(CHINOOK_URL, output_path)
        print("✅ Download complete!")
    except Exception as e:
        print(f"❌ Error downloading database: {e}")
        raise


def inspect_database(db_path: Path) -> None:
    """Print database schema and statistics.

    Args:
        db_path: Path to SQLite database
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()

    print("\n" + "=" * 60)
    print("DATABASE SCHEMA")
    print("=" * 60)

    for (table_name,) in tables:
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]

        # Get column info
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()

        print(f"\n📊 {table_name} ({count:,} rows)")
        print("-" * 60)
        for col in columns:
            col_id, name, col_type, not_null, default, pk = col
            pk_marker = " 🔑 PK" if pk else ""
            null_marker = " NOT NULL" if not_null else ""
            print(f"  • {name}: {col_type}{null_marker}{pk_marker}")

    # Sample queries to demonstrate data
    print("\n" + "=" * 60)
    print("SAMPLE DATA")
    print("=" * 60)

    print("\n🎵 Top 5 Artists by Track Count:")
    cursor.execute("""
        SELECT Artist.Name, COUNT(Track.TrackId) as TrackCount
        FROM Artist
        JOIN Album ON Artist.ArtistId = Album.ArtistId
        JOIN Track ON Album.AlbumId = Track.AlbumId
        GROUP BY Artist.ArtistId
        ORDER BY TrackCount DESC
        LIMIT 5
    """)
    for name, count in cursor.fetchall():
        print(f"  • {name}: {count} tracks")

    print("\n💿 Albums:")
    cursor.execute("SELECT Title FROM Album LIMIT 5")
    for (title,) in cursor.fetchall():
        print(f"  • {title}")

    print("\n🎧 Genres:")
    cursor.execute("SELECT Name FROM Genre LIMIT 8")
    for (name,) in cursor.fetchall():
        print(f"  • {name}")

    print("\n💰 Total Sales:")
    cursor.execute("SELECT SUM(Total) as TotalSales FROM Invoice")
    total = cursor.fetchone()[0]
    print(f"  ${total:,.2f}")

    print("\n👥 Customer Countries:")
    cursor.execute("""
        SELECT Country, COUNT(*) as CustomerCount
        FROM Customer
        GROUP BY Country
        ORDER BY CustomerCount DESC
        LIMIT 5
    """)
    for country, count in cursor.fetchall():
        print(f"  • {country}: {count} customers")

    conn.close()


def main():
    """Download and setup Chinook database."""
    # Use same location as test database
    db_path = Path(__file__).parent.parent / "test_chinook.db"

    print("=" * 60)
    print("CHINOOK DATABASE SETUP")
    print("=" * 60)
    print()
    print("The Chinook database represents a digital media store.")
    print("It contains data about artists, albums, tracks, customers,")
    print("invoices, and more. Great for testing SQL agent capabilities!")
    print()

    # Remove existing database if present
    if db_path.exists():
        print(f"⚠️  Removing existing database: {db_path}")
        db_path.unlink()

    # Download database
    download_chinook_db(db_path)

    # Verify download and show schema
    file_size = db_path.stat().st_size / (1024 * 1024)  # Convert to MB
    print(f"\n✅ Database file size: {file_size:.2f} MB")

    # Inspect database
    inspect_database(db_path)

    # Print connection string
    abs_path = db_path.resolve()
    print("\n" + "=" * 60)
    print("NEXT STEPS")
    print("=" * 60)
    print("\n1. Update your .env file:")
    print(f"   SNOWFLAKE_AGENT_SNOWFLAKE_URI=sqlite:///{abs_path}")
    print("\n2. Or set environment variable:")
    print(f"   export SNOWFLAKE_AGENT_SNOWFLAKE_URI=sqlite:///{abs_path}")
    print("\n3. Start the dev server:")
    print("   make dev")
    print("\n4. Try example queries in LangGraph Studio:")
    print("   • 'Show me all tables'")
    print("   • 'Who are the top 10 artists by track count?'")
    print("   • 'What are total sales by country?'")
    print("   • 'List the most expensive tracks'")
    print("   • 'Show me customers who spent the most'")
    print("   • 'What are the most popular genres?'")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
