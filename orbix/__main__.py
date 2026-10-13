import argparse
import sys
from pathlib import Path

from orbix.config import Config
from orbix.pipeline import Pipeline


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="orbix",
        description="Orbix: Intelligent Measurement for Modern Mills",
    )

    parser.add_argument(
        "--source",
        default="0",
        help="camera index (integer) or path to video file (default: 0)",
    )
    parser.add_argument(
        "--model",
        default="yolov8n.pt",
        help="path to YOLO model weights (default: yolov8n.pt)",
    )
    parser.add_argument(
        "--confidence",
        type=float,
        default=0.25,
        help="minimum detection confidence threshold (default: 0.25)",
    )
    parser.add_argument(
        "--output-dir",
        default="data/logs",
        help="directory for CSV log output (default: data/logs)",
    )
    parser.add_argument(
        "--no-display",
        action="store_true",
        help="disable visualization window",
    )
    parser.add_argument(
        "--windowed",
        action="store_true",
        help="run in windowed mode instead of fullscreen",
    )

    return parser.parse_args(argv)


def _parse_source(source_str: str) -> int | str:
    try:
        return int(source_str)
    except ValueError:
        return source_str


def main(argv: list[str] | None = None):
    args = parse_args(argv)

    source = _parse_source(args.source)

    try:
        config = Config(
            source=source,
            model_path=args.model,
            confidence_threshold=args.confidence,
            output_dir=Path(args.output_dir),
            display=not args.no_display,
            fullscreen=not args.windowed,
        )
    except (ValueError, TypeError) as exc:
        print(f"[ERROR] Invalid configuration: {exc}", file=sys.stderr)
        sys.exit(1)

    if config.display:
        try:
            from orbix.bridge import WebviewApp
            app = WebviewApp(config)
            app.run()
            return
        except Exception:
            pass

    pipeline = Pipeline(config)
    pipeline.run()


if __name__ == "__main__":
    main()
