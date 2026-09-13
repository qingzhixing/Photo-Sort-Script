#!/usr/bin/python3

# 照片整理脚本
# -i INPUT_DIR -o OUTPUT_DIR

import argparse
import datetime
import os
import subprocess
import sys
from collections import defaultdict

from PIL import Image
from PIL.ExifTags import TAGS


def _ensure_heif_support() -> bool:
    """确保 HEIF/HEIC 支持可用，如未安装则自动安装并返回是否成功。"""
    try:
        from pillow_heif.as_plugin import register_heif_opener

        register_heif_opener()
        return True
    except ImportError:
        print("[提示] 未检测到 pillow-heif，HEIC/HEIF 格式支持不可用。")
        print("[提示] 正在尝试自动安装 pillow-heif...")
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "pillow-heif", "-q"]
            )
            # 安装后重新导入
            from pillow_heif.as_plugin import register_heif_opener

            register_heif_opener()
            print("[提示] pillow-heif 安装成功，HEIC/HEIF 支持已启用。")
            return True
        except subprocess.CalledProcessError:
            print("[错误] 自动安装 pillow-heif 失败。")
            print("[提示] 请手动运行: pip install pillow-heif")
            return False
        except ImportError:
            print("[错误] 安装后仍无法导入 pillow_heif，请检查 Python 环境。")
            return False


_HEIF_SUPPORT = _ensure_heif_support()


def _parse_exif_datetime(value: str) -> datetime.datetime:
    """解析 EXIF 日期字符串为 aware datetime（使用系统本地时区）。"""
    naive = datetime.datetime.strptime(  # noqa: DTZ007
        value, "%Y:%m:%d %H:%M:%S"
    )
    return naive.replace(tzinfo=datetime.timezone.utc).astimezone()


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


def get_exif_date(file_path: str) -> datetime.datetime | None:
    """获取照片的拍摄日期（EXIF DateTimeOriginal），如果获取失败返回 None"""
    try:
        with Image.open(file_path) as img:
            exif_data = img.getexif()
            if exif_data is None:
                return None

            # 查找 DateTimeOriginal 标签
            for tag_id, value in exif_data.items():
                tag_name = TAGS.get(tag_id, tag_id)
                if tag_name == "DateTimeOriginal":
                    # EXIF 日期格式: "YYYY:MM:DD HH:MM:SS"
                    return _parse_exif_datetime(value)

            # 如果没有 DateTimeOriginal，尝试 DateTimeDigitized
            for tag_id, value in exif_data.items():
                tag_name = TAGS.get(tag_id, tag_id)
                if tag_name == "DateTimeDigitized":
                    return _parse_exif_datetime(value)

            # 最后尝试 DateTime
            for tag_id, value in exif_data.items():
                tag_name = TAGS.get(tag_id, tag_id)
                if tag_name == "DateTime":
                    return _parse_exif_datetime(value)

            return None
    except (OSError, ValueError):
        return None


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
    print(
        "HEIF/HEIC 支持: ",
        "已启用" if _HEIF_SUPPORT else "未安装 (pip install pillow-heif)",
    )

    if not os.path.exists(source_folder):
        print(f'输入文件夹: "{source_folder}" 不存在')
        sys.exit(1)

    # 创建目标文件夹
    os.makedirs(target_folder, exist_ok=True)

    # 将文件按日期分类
    date_files = defaultdict(list)
    no_exif_files = []

    # 遍历文件
    for filename in os.listdir(source_folder):
        file_path = os.path.join(source_folder, filename)

        # 跳过目录
        if os.path.isdir(file_path):
            continue

        # 获取 EXIF 拍摄日期
        file_date = get_exif_date(file_path)

        if file_date is not None:
            file_key = file_date.strftime("%Y.%m.%d")
            date_files[file_key].append((file_path, filename, file_date))
        else:
            no_exif_files.append((file_path, filename))

    total_files = sum(len(photos) for photos in date_files.values()) + len(
        no_exif_files
    )

    print(f"共处理 {total_files} 个文件")
    print(
        f"  - 有 EXIF 拍摄日期: {sum(len(photos) for photos in date_files.values())} 个"
    )
    print(f"  - 无 EXIF 拍摄日期: {len(no_exif_files)} 个")

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
            except OSError as e:
                print(f"  移动 {filename} 时出错: {e}")

    # 处理无 EXIF 日期的文件
    if no_exif_files:
        no_exif_folder = os.path.join(target_folder, "无拍摄日期")
        os.makedirs(no_exif_folder, exist_ok=True)
        print(
            f"\n无 EXIF 拍摄日期的文件 {len(no_exif_files)} 个，移动到: {no_exif_folder}"
        )

        for file_path, filename in no_exif_files:
            try:
                target_file_path = os.path.join(no_exif_folder, filename)

                # 若目标文件存在则添加数字后缀
                base, ext = os.path.splitext(filename)
                counter = 1
                while os.path.exists(target_file_path):
                    target_file_path = os.path.join(
                        no_exif_folder, f"{base}_{counter}{ext}"
                    )
                    counter += 1

                # 移动文件
                os.rename(file_path, target_file_path)
                print(f"移动文件 {filename} 到 {no_exif_folder}")
            except OSError as e:
                print(f"  移动 {filename} 时出错: {e}")
