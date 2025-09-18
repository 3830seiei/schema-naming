#!/usr/bin/env python3
"""
特定のYAMLファイルだけを変換するスクリプト

Usage: python yaml_rename_specific.py file1.yaml file2.yaml
"""

import yaml
import sys
from pathlib import Path
from datetime import datetime

# メインのyaml_rename.pyから必要な関数をインポート
from yaml_rename import load_rename_dictionary, process_yaml_file, save_converted_yaml


def main():
    """特定ファイルのみを変換"""
    if len(sys.argv) < 2:
        print("Usage: python yaml_rename_specific.py file1.yaml file2.yaml ...")
        sys.exit(1)

    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    # パス設定
    input_dir = project_root / 'tools/config/smds_poc'
    rename_dict_path = project_root / 'dictionary/rename_dictionary.yaml'
    output_dir = project_root / 'tools/config/streamedix'

    # rename_dictionary.yamlを読み込み
    if not rename_dict_path.exists():
        print(f"Error: {rename_dict_path} が見つかりません")
        sys.exit(1)

    print(f"変換辞書を読み込み中: {rename_dict_path}")
    rename_dict = load_rename_dictionary(rename_dict_path)

    # 指定されたファイルを処理
    target_files = sys.argv[1:]
    print(f"処理対象ファイル: {target_files}")

    conversion_stats = {
        'total_files': len(target_files),
        'success_count': 0,
        'failed_count': 0,
        'table_renamed': 0,
        'columns_renamed': 0
    }

    for filename in target_files:
        yaml_file = input_dir / filename

        if not yaml_file.exists():
            print(f"エラー: {yaml_file} が見つかりません")
            conversion_stats['failed_count'] += 1
            continue

        print(f"\n処理中: {filename}")

        try:
            # YAMLファイルを変換
            converted_data, conv_stats, original_table, new_table = process_yaml_file(yaml_file, rename_dict)

            # 出力ファイル名を新しいテーブル名で決定
            output_file = output_dir / f"{new_table}.yaml"

            # 変換されたYAMLを保存
            save_converted_yaml(converted_data, output_file)

            # 統計を更新
            conversion_stats['success_count'] += 1
            if original_table != new_table:
                conversion_stats['table_renamed'] += 1

            columns_converted = conv_stats['columns_converted']
            conversion_stats['columns_renamed'] += columns_converted

            print(f"  → 保存: {output_file}")
            print(f"  → テーブル名: {original_table} → {new_table}")
            print(f"  → カラム変換数: {columns_converted}")

        except Exception as e:
            print(f"  → エラー: {e}")
            conversion_stats['failed_count'] += 1

    print(f"\n=== 変換完了 ===")
    print(f"成功: {conversion_stats['success_count']}/{conversion_stats['total_files']}個")
    print(f"テーブル名変換: {conversion_stats['table_renamed']}個")
    print(f"カラム名変換: {conversion_stats['columns_renamed']}個")


if __name__ == '__main__':
    main()