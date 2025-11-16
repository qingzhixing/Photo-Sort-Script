#!/usr/bin/python3
# 展开所有子文件夹

import argparse
import os


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Photo Sort")
    parser.add_argument("-i", "--input", type=str, required=True, help="Input folder")
    parser.add_argument(
        "-o", "--output", type=str, required=False, help="Output folder"
    )

    args = parser.parse_args()
    input_folder = args.input
    target_folder = args.output if args.output else input_folder

    if args.output is None:
        print(f"默认展开所有子文件夹到文件夹: {input_folder}")

    # 遍历所有子文件夹
    for root, dirs, files in os.walk(input_folder):
        for dir in dirs:
            dir_path = os.path.join(root, dir)
            print(f"找到子文件夹: {dir_path}")

            # 展开子文件夹到目标文件夹
            # 遍历子文件夹中的文件/文件夹
            for item in os.listdir(dir_path):
                item_path = os.path.join(dir_path, item)
                target_item_path = os.path.join(target_folder, item)
                print(f"复制 {item_path} 到 {target_item_path}")
                os.rename(item_path, target_item_path)

            # 删除原文件夹
            os.rmdir(dir_path)
