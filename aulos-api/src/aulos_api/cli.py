import argparse

import uvicorn

from aulos_api.config import get_settings


def main() -> None:
    parser = argparse.ArgumentParser(description="Aulos API gateway")
    parser.add_argument("--host", default=None)
    parser.add_argument("--port", type=int, default=None)
    args = parser.parse_args()
    settings = get_settings()
    uvicorn.run(
        "aulos_api.app:app",
        host=args.host or settings.host,
        port=args.port or settings.port,
        reload=False,
    )


if __name__ == "__main__":
    main()
