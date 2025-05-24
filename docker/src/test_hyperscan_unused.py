#!/usr/bin/env python3
import sys
import os


def main():
    try:
        print("Python version:", sys.version)
        print("Current working directory:", os.getcwd())
        print("Contents of current directory:", os.listdir("."))

        print("\nAttempting to import hyperscan...")
        import hyperscan

        print("Successfully imported hyperscan")
        print("Hyperscan version:", hyperscan.__version__)

        # Create a database
        print("\nCreating database...")
        db = hyperscan.Database()

        # Define a simple pattern
        pattern = rb"fo+"
        print(f"Using pattern: {pattern}")

        # Compile pattern
        print("\nCompiling pattern...")
        db.compile(expressions=[pattern], ids=[0], elements=1)

        # Print database info
        print("\nDatabase info:")
        print(db.info().decode())

        # Test scanning
        print("\nTesting basic scanning:")
        db.scan(
            b"foobar",
            match_event_handler=lambda id, from_pos, to_pos, flags, context: print(
                f"Match found: id={id}, from={from_pos}, to={to_pos}"
            ),
        )

        print("\nTest completed successfully!")

    except Exception as e:
        print(f"\nError occurred: {str(e)}")
        print("\nFull error details:")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
