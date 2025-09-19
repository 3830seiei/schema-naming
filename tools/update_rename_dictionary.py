#!/usr/bin/env python3
"""
optiserveテーブル定義からrename_dictionary.yamlを更新するスクリプト

- tables: 既存のキーをnewにもセット（# optiserve v2追加）
- columns: 既存項目があればマッチング、なければ同名セット（# claude-code set）
"""

import yaml
import os
from pathlib import Path
from datetime import datetime


def load_yaml_file(file_path):
    """YAMLファイルを読み込む"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None


def find_matching_column(column_name, existing_columns):
    """
    既存のcolumnsから類似する項目を探す
    返り値: (match_found, suggested_new_name)
    """
    # 完全一致
    for table_name, table_columns in existing_columns.items():
        for col_name, col_info in table_columns.items():
            if col_name == column_name:
                return True, col_info['new']

    # 部分一致または類似名での検索
    common_mappings = {
        'id': 'id',
        'user_id': 'user_id',
        'facility_id': 'medical_facility_id',
        'medical_facility_id': 'medical_facility_id',
        'created_at': 'created_at',
        'updated_at': 'updated_at',
        'created_by': 'created_by',
        'updated_by': 'updated_by',
        'name': 'name',
        'description': 'description',
        'status': 'status',
        'is_active': 'is_active',
        'sort_order': 'sort_order',
        'display_order': 'display_order'
    }

    if column_name in common_mappings:
        return True, common_mappings[column_name]

    # 完全一致がない場合は同名を提案
    return False, column_name


def process_optiserve_files():
    """optiserveファイルを処理してrename_dictionary用のデータを生成"""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    optiserve_dir = project_root / 'tools/config/optiserve'

    tables_data = {}
    columns_data = {}

    # YAMLファイルを取得（database始まりは除外）
    yaml_files = [f for f in optiserve_dir.glob('*.yaml') if not f.name.startswith('database')]

    print(f"処理対象ファイル: {len(yaml_files)}個")

    for yaml_file in yaml_files:
        print(f"処理中: {yaml_file.name}")

        yaml_data = load_yaml_file(yaml_file)
        if not yaml_data:
            continue

        # table_nameを取得
        table_name = yaml_data.get('table_name', '')
        if not table_name:
            print(f"  table_nameが見つかりません")
            continue

        description = yaml_data.get('description', '')

        # tablesデータに追加
        tables_data[table_name] = {
            'new': table_name,  # 既存名をnewにもセット
            'description': description
        }

        # columnsデータを処理
        columns = yaml_data.get('columns', [])
        if columns:
            columns_data[table_name] = {}
            for col in columns:
                col_name = col.get('name', '')
                col_desc = col.get('description', '')
                if col_name:
                    columns_data[table_name][col_name] = {
                        'new': col_name,  # 初期値として同名をセット
                        'description': col_desc
                    }

    return tables_data, columns_data


def update_rename_dictionary(new_tables, new_columns):
    """rename_dictionary.yamlを更新"""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    dict_path = project_root / 'dictionary/rename_dictionary.yaml'

    # 既存の辞書を読み込み
    print(f"既存辞書を読み込み: {dict_path}")
    existing_dict = load_yaml_file(dict_path)
    if not existing_dict:
        print("既存辞書の読み込みに失敗")
        return False

    existing_tables = existing_dict.get('tables', {})
    existing_columns = existing_dict.get('columns', {})

    print(f"既存tables: {len(existing_tables)}個")
    print(f"既存columns: {len(existing_columns)}個")

    # tablesセクションを更新
    tables_added = 0
    for table_name, table_info in new_tables.items():
        if table_name not in existing_tables:
            existing_tables[f"{table_name}"] = {
                'new': table_info['new'],
                'description': f"{table_info['description']} # optiserve v2追加"
            }
            tables_added += 1
            print(f"  tables追加: {table_name}")

    # columnsセクションを更新
    columns_added = 0
    for table_name, table_columns in new_columns.items():
        if table_name not in existing_columns:
            existing_columns[table_name] = {}

        for col_name, col_info in table_columns.items():
            if col_name not in existing_columns[table_name]:
                # 既存columnsから類似項目を検索
                match_found, suggested_new = find_matching_column(col_name, existing_columns)

                comment = " # claude-code set" if match_found else " # optiserve v2追加"

                existing_columns[table_name][col_name] = {
                    'new': suggested_new,
                    'description': f"{col_info['description']}{comment}"
                }
                columns_added += 1
                print(f"  columns追加: {table_name}.{col_name} -> {suggested_new}")

    # 更新された辞書を保存
    existing_dict['tables'] = existing_tables
    existing_dict['columns'] = existing_columns

    # バックアップファイル名
    backup_path = dict_path.with_suffix(f'.yaml.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}')

    try:
        # 現在のファイルをバックアップ
        with open(dict_path, 'r', encoding='utf-8') as src, \
             open(backup_path, 'w', encoding='utf-8') as dst:
            dst.write(src.read())

        # 更新されたファイルを保存
        with open(dict_path, 'w', encoding='utf-8') as f:
            yaml.dump(existing_dict, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

        print(f"\n更新完了:")
        print(f"  tables追加: {tables_added}個")
        print(f"  columns追加: {columns_added}個")
        print(f"  バックアップ: {backup_path.name}")
        return True

    except Exception as e:
        print(f"ファイル保存エラー: {e}")
        return False


def main():
    """メイン処理"""
    print("optiserveテーブル定義からrename_dictionary.yaml更新処理を開始")
    print("="*60)

    # optiserveファイルを処理
    new_tables, new_columns = process_optiserve_files()

    if not new_tables:
        print("処理対象のテーブルが見つかりませんでした")
        return

    print(f"\n抽出結果:")
    print(f"  新規tables: {len(new_tables)}個")
    print(f"  新規columns: {sum(len(cols) for cols in new_columns.values())}個")

    # rename_dictionary.yamlを更新
    if update_rename_dictionary(new_tables, new_columns):
        print("\n処理が正常に完了しました")
    else:
        print("\n処理中にエラーが発生しました")


if __name__ == '__main__':
    main()