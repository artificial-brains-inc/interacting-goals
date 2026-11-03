"""Application entry point discovered by ab run -ab --env .env."""
from goals.application import main

if __name__ == "__main__":
    raise SystemExit(main())
