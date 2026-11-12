"""Run the small-instance replay-retention reference model."""
import argparse
import json
from pathlib import Path
from reference_impl.replay_core import RetentionInstance


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path,
                        default=Path('data/examples/replay_profiles.json'),
                        help='Input profile catalog in JSON format')
    parser.add_argument('--mode', choices=('budget', 'price'), default='budget',
                        help='Optimize utility under a budget, or utility minus price × cost')
    parser.add_argument('--price', type=int, default=0,
                        help='Nonnegative storage price for --mode price')
    parser.add_argument('--cap', type=int, default=1000000,
                        help='Maximum number of enumerated profile combinations')
    args = parser.parse_args()
    if args.price < 0 or args.cap < 1:
        parser.error('--price must be nonnegative and --cap must be at least 1')
    if args.mode != 'price' and args.price != 0:
        parser.error('--price is only applicable with --mode price')
    try:
        instance = RetentionInstance(json.loads(args.input.read_text(encoding='utf-8')))
        results = {
            'status': 'small_instance_reference_only',
            'raw': instance.optimize(mode=args.mode, price=args.price, cap=args.cap),
            'quotient': instance.optimize(mode=args.mode, price=args.price,
                                          compressed='quotient', cap=args.cap),
            'skyline': instance.optimize(mode=args.mode, price=args.price,
                                         compressed='skyline', cap=args.cap),
        }
    except (OSError, ValueError, KeyError, TypeError, OverflowError) as exc:
        parser.exit(2, f'Error: {exc}\n')
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
