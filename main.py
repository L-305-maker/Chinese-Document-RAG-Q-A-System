import argparse
import sys

def build_parse():
    parser = argparse.ArgumentParser(description="question and answer")
    parser.add_argument(
        "--input_file_path",
        type=str,
        help = "问题的输入路径"
    )

    parser.add_argument(
        "--output-file_path",
        type=str,
        default="output.txt",
        help="这是回答的存储路径"
    )

    parser.add_argument(
        "--mode",
        choices=["ingestion","Q&A"],
        help="选择你需要进行的任务"
    )

    parser.add_argument(
        "--help",
        action= "store_true",
        help="show this help message and exit"
    )

    args = parser.parse_args()

    return args


def parse_args(args = None):
    parser = build_parse()
    args,remaining_args = parser.parse_known_args(args)

    if args.help and args.mode is None:
        parser.print_help()
        sys.exit()

    if args.mode is None:
        parser.error("the following arguments are required: --mode")

    if args.help:
        remaining_args.insert(0,"--help")

    return args,remaining_args

def main():
    args,remaining_args = parse_args()

    task_name = args.mode