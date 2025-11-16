#!/usr/bin/python3
import argparse
from collections import defaultdict
import datetime
import os

# 定义阈值，当日文件数量超过该值，才会创建当天文件夹
THRESHOLD = 20


def get_week_folder_name(file_date: datetime.datetime) -> str:
    week_start = file_date - datetime.timedelta(days=file_date.weekday())
    week_end = week_start + datetime.timedelta(days=6)
    week_number = week_start.isocalendar()[1]
    week_folder_name = ""
    if week_start.year == week_end.year:
        week_folder_name = f"{week_start.strftime('%Y.%m.%d')} 至 {week_end.strftime('%m.%d')} 第{week_number}周"
    else:
        week_folder_name = f"{week_start.strftime('%Y.%m.%d')} 至 {week_end.strftime('%Y.%m.%d')} 第{week_number}周"

    return week_folder_name


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Photo Sort")
    parser.add_argument("-i", "--input", type=str, required=True, help="Input folder")
    parser.add_argument(
        "-o", "--output", type=str, required=False, help="Output folder"
    )
    args = parser.parse_args()
    source_folder = args.input
    target_folder = args.output if args.output else source_folder

    if args.output is None:
        print("默认输出文件夹为: ", source_folder)

    print("待整理文件夹: ", source_folder)
    print("输出文件夹: ", target_folder)

    if not os.path.exists(source_folder):
        print('输入文件夹: "%s" 不存在' % source_folder)
        exit(1)

    # 创建目标文件夹
    os.makedirs(target_folder, exist_ok=True)

    # 将文件按日期分类
    date_files = defaultdict(list)

    # 遍历文件
    for filename in os.listdir(source_folder):
        file_path = os.path.join(source_folder, filename)

        # 跳过目录
        if os.path.isdir(file_path):
            continue

        # 按修改时间分类
        try:
            mod_time = os.path.getmtime(file_path)
            file_date: datetime.datetime = datetime.datetime.fromtimestamp(mod_time)
            file_key = file_date.strftime("%Y.%m.%d")
            date_files[file_key].append((file_path, filename, file_date))

        except Exception as e:
            print(f"处理文件 {file_path} 时出错: {e}")
            continue

    total_files = sum(len(photos) for photos in date_files.values())

    print(f"共处理 {total_files} 个文件")

    # 处理每个日期的图片，并移动到目标文件夹
    for file_key, files in date_files.items():
        print(f"日期 {file_key} 共 {len(files)} 张图片")

        # 提取第一个文件的日期
        _, _, file_date = files[0]

        # 创建周文件夹名称
        week_folder_name = get_week_folder_name(file_date)
        week_folder_path = os.path.join(target_folder, week_folder_name)

        # 当日文件夹名称
        day_folder_name = file_date.strftime(file_key)
        day_folder_path = os.path.join(target_folder, day_folder_name)

        current_folder_path = week_folder_path

        # 检查该日照片数量
        if len(files) >= THRESHOLD:
            print(
                f"日期 {file_key} 共 {len(files)} 张图片，超过阈值 {THRESHOLD}，创建当日文件夹"
            )
            current_folder_path = day_folder_path

        os.makedirs(current_folder_path, exist_ok=True)

        # 移动文件到目标文件夹
        for file_path, filename, _ in files:
            try:
                target_file_path = os.path.join(current_folder_path, filename)

                # 若目标文件存在则添加数字后缀
                base, ext = os.path.splitext(filename)
                counter = 1
                while os.path.exists(target_file_path):
                    target_file_path = os.path.join(
                        current_folder_path, f"{base}_{counter}{ext}"
                    )
                    counter += 1

                # 移动文件
                os.rename(file_path, target_file_path)
                print(f"移动文件 {filename} 到 {current_folder_path}")
            except Exception as e:
                print(f"  移动 {filename} 时出错: {e}")
