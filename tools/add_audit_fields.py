#!/usr/bin/env python3
"""
config/streamedix/core,cur,raw/*.yamlファイルに監査フィールドを追加するスクリプト

追加するフィールド:
- created_by (TEXT): 作成者ID（ユーザーID・システムID）
- updated_by (TEXT): 最終更新者ID（ユーザーID・システムID）

フィールドの並び順: created_at, created_by, updated_at, updated_by
"""

import yaml
import os
from pathlib import Path
from datetime import datetime


def add_audit_fields_to_columns(columns):
    """
    columnsリストに監査フィールド(created_by, updated_by)を追加する
    created_at, updated_atが既にあることを前提に、適切な位置に挿入する
    """
    if not columns:
        return columns

    # 既存の監査フィールドのインデックスを探す
    created_at_idx = None
    updated_at_idx = None
    created_by_exists = False
    updated_by_exists = False

    for i, col in enumerate(columns):
        name = col.get('name', '')
        if name == 'created_at':
            created_at_idx = i
        elif name == 'updated_at':
            updated_at_idx = i
        elif name == 'created_by':
            created_by_exists = True
        elif name == 'updated_by':
            updated_by_exists = True

    # 既に存在する場合はスキップ
    if created_by_exists and updated_by_exists:
        print("    監査フィールドは既に存在します")
        return columns

    # created_byフィールドの定義
    created_by_field = {
        'name': 'created_by',
        'data_type': 'TEXT',
        'nullable': False,
        'description': '作成者ID（ユーザーID・システムID）'
    }

    # updated_byフィールドの定義
    updated_by_field = {
        'name': 'updated_by',
        'data_type': 'TEXT',
        'nullable': False,
        'description': '最終更新者ID（ユーザーID・システムID）'
    }

    # 新しいcolumnsリストを作成
    new_columns = []

    for i, col in enumerate(columns):
        new_columns.append(col)

        # created_atの直後にcreated_byを挿入
        if i == created_at_idx and not created_by_exists:
            new_columns.append(created_by_field)
            print("    created_byフィールドを追加")

        # updated_atの直後にupdated_byを挿入
        if i == updated_at_idx and not updated_by_exists:
            new_columns.append(updated_by_field)
            print("    updated_byフィールドを追加")

    return new_columns


def process_yaml_file(file_path):
    """YAMLファイルを処理して監査フィールドを追加"""
    print(f"\n処理中: {file_path.name}")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            yaml_data = yaml.safe_load(f)

        if not yaml_data:
            print("    YAMLデータが空です")
            return False

        # columnsが存在するかチェック
        if 'columns' not in yaml_data or not yaml_data['columns']:
            print("    columnsセクションが見つかりません")
            return False

        # 監査フィールドを追加
        original_count = len(yaml_data['columns'])
        yaml_data['columns'] = add_audit_fields_to_columns(yaml_data['columns'])
        new_count = len(yaml_data['columns'])

        if new_count > original_count:
            # ファイルを更新
            with open(file_path, 'w', encoding='utf-8') as f:
                # ヘッダーコメント
                f.write('#- metadata -----------------------------------------------\n')

                # YAMLデータを整形して出力
                yaml_str = yaml.dump(yaml_data,
                                   default_flow_style=False,
                                   allow_unicode=True,
                                   sort_keys=False,
                                   indent=2)

                # セクション区切りを追加
                lines = yaml_str.split('\n')
                result_lines = []

                for i, line in enumerate(lines):
                    if line.startswith('table_name:'):
                        result_lines.append('\n#- tableinfo ----------------------------------------------')
                    elif line.startswith('columns:'):
                        result_lines.append('\n#- columns info -------------------------------------------')

                    result_lines.append(line)

                f.write('\n'.join(result_lines))

            print(f"    ファイルを更新しました ({original_count} → {new_count} columns)")
            return True
        else:
            print("    変更はありませんでした")
            return False

    except Exception as e:
        print(f"    エラー: {e}")
        return False


def main():
    """メイン処理"""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    # 対象ディレクトリ
    target_dirs = [
        project_root / 'tools/config/streamedix/core',
        project_root / 'tools/config/streamedix/cur',
        project_root / 'tools/config/streamedix/raw'
    ]

    total_files = 0
    updated_files = 0

    print("監査フィールド追加処理を開始します")
    print("追加フィールド: created_by (TEXT), updated_by (TEXT)")
    print("="*60)

    for target_dir in target_dirs:
        if not target_dir.exists():
            print(f"\nディレクトリが見つかりません: {target_dir}")
            continue

        print(f"\n処理ディレクトリ: {target_dir}")

        # YAMLファイルを取得
        yaml_files = list(target_dir.glob('*.yaml'))

        if not yaml_files:
            print("  YAMLファイルが見つかりません")
            continue

        print(f"  対象ファイル数: {len(yaml_files)}個")

        for yaml_file in yaml_files:
            total_files += 1
            if process_yaml_file(yaml_file):
                updated_files += 1

    print("\n" + "="*60)
    print(f"処理完了")
    print(f"処理対象ファイル数: {total_files}個")
    print(f"更新されたファイル数: {updated_files}個")
    print(f"処理日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == '__main__':
    main()