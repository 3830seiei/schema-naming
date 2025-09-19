#!/usr/bin/env python3
"""
既存YAMLファイルをrename_dictionary.yamlで変換するスクリプト

Input: tools/config/optiserve/*.yaml（既存opiserveファイル）
Process: dictionary/rename_dictionary.yamlの変換ルールを適用
Output: tools/config/streamedix/optiserve/*.yaml（新命名）
"""

import yaml
import os
import sys
from pathlib import Path
from datetime import datetime


def load_rename_dictionary(rename_dict_path):
    """rename_dictionary.yamlを読み込む"""
    with open(rename_dict_path, 'r', encoding='utf-8') as f:
        rename_dict = yaml.safe_load(f)

    return rename_dict


def rename_table_name(table_name, rename_dict):
    """テーブル名を変換"""
    tables_dict = rename_dict.get('tables', {})

    if table_name in tables_dict:
        return tables_dict[table_name]['new']

    return table_name  # 変換ルールがない場合はそのまま


def rename_column_name(table_name, column_name, rename_dict):
    """カラム名を変換"""
    columns_dict = rename_dict.get('columns', {})

    # テーブル固有のカラム変換ルールを確認
    if table_name in columns_dict:
        table_columns = columns_dict[table_name]
        if column_name in table_columns:
            return table_columns[column_name]['new']

    return column_name  # 変換ルールがない場合はそのまま


def process_yaml_file(input_path, rename_dict):
    """YAMLファイルを処理して変換（オリジナルのname/old_nameフィールドを直接変更）"""
    with open(input_path, 'r', encoding='utf-8') as f:
        yaml_data = yaml.safe_load(f)

    # テーブル名を変換
    original_table_name = yaml_data.get('table_name', '')
    new_table_name = rename_table_name(original_table_name, rename_dict)

    # テーブル名を新しい名前に変更
    yaml_data['table_name'] = new_table_name

    # メタデータに変換情報を追加
    if 'metadata' not in yaml_data:
        yaml_data['metadata'] = {}

    yaml_data['metadata']['conversion_info'] = {
        'source_file': str(input_path.name),
        'original_table_name': original_table_name,
        'conversion_date': datetime.now().strftime('%Y-%m-%d'),
        'applied_rules': 'rename_dictionary.yaml v1'
    }

    # カラム情報を変換（既存の構造を保持しつつ、nameフィールドのみ変更）
    original_columns = yaml_data.get('columns', [])
    conversion_stats = {'columns_converted': 0}

    for col in original_columns:
        original_name = col.get('name', '')
        new_name = rename_column_name(original_table_name, original_name, rename_dict)

        if original_name != new_name:
            # old_nameが未設定の場合、元のnameを記録
            if 'old_name' not in col or col.get('old_name') == original_name:
                col['old_name'] = original_name

            # nameフィールドを新しい名前に変更
            col['name'] = new_name
            conversion_stats['columns_converted'] += 1

    return yaml_data, conversion_stats, original_table_name, new_table_name


def save_converted_yaml(yaml_data, output_path):
    """変換されたYAMLファイルを保存"""
    # ディレクトリを作成
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
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


def generate_conversion_report(conversion_stats, output_dir):
    """変換レポートを生成"""
    report_path = output_dir / 'conversion_report.md'

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(f'# YAML変換レポート\n\n')
        f.write(f'変換日時: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n\n')
        f.write(f'## 変換サマリー\n\n')
        f.write(f'- 処理対象ファイル数: {conversion_stats["total_files"]}\n')
        f.write(f'- 変換成功: {conversion_stats["success_count"]}\n')
        f.write(f'- 変換失敗: {conversion_stats["failed_count"]}\n')
        f.write(f'- テーブル名変換: {conversion_stats["table_renamed"]}\n')
        f.write(f'- カラム名変換: {conversion_stats["columns_renamed"]}\n\n')

        if conversion_stats["conversions"]:
            f.write(f'## 変換詳細\n\n')
            for conv in conversion_stats["conversions"]:
                f.write(f'### {conv["original_file"]}\n')
                f.write(f'- 元テーブル名: `{conv["original_table"]}`\n')
                f.write(f'- 新テーブル名: `{conv["new_table"]}`\n')
                f.write(f'- カラム変換数: {conv["columns_converted"]}\n')
                f.write(f'- 出力ファイル: `{conv["output_file"]}`\n\n')

        if conversion_stats["errors"]:
            f.write(f'## エラー詳細\n\n')
            for error in conversion_stats["errors"]:
                f.write(f'- {error["file"]}: {error["error"]}\n')


def main():
    """メイン処理"""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    # パス設定
    input_dir = project_root / 'tools/config/optiserve'
    rename_dict_path = project_root / 'dictionary/rename_dictionary.yaml'
    output_dir = project_root / 'tools/config/streamedix/optiserve'

    # rename_dictionary.yamlを読み込み
    if not rename_dict_path.exists():
        print(f"Error: {rename_dict_path} が見つかりません")
        sys.exit(1)

    print(f"変換辞書を読み込み中: {rename_dict_path}")
    rename_dict = load_rename_dictionary(rename_dict_path)

    # 入力ディレクトリの確認
    if not input_dir.exists():
        print(f"Error: {input_dir} が見つかりません")
        sys.exit(1)

    # YAMLファイルを取得（.xlsxは除外）
    yaml_files = [f for f in input_dir.glob('*.yaml')]

    if not yaml_files:
        print(f"Error: {input_dir} にYAMLファイルが見つかりません")
        sys.exit(1)

    print(f"処理対象ファイル: {len(yaml_files)}個")

    # 変換統計
    conversion_stats = {
        'total_files': len(yaml_files),
        'success_count': 0,
        'failed_count': 0,
        'table_renamed': 0,
        'columns_renamed': 0,
        'conversions': [],
        'errors': []
    }

    # 各ファイルを処理
    for yaml_file in yaml_files:
        print(f"\n処理中: {yaml_file.name}")

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

            conversion_stats['conversions'].append({
                'original_file': yaml_file.name,
                'original_table': original_table,
                'new_table': new_table,
                'columns_converted': columns_converted,
                'output_file': output_file.name
            })

            print(f"  → 保存: {output_file}")
            print(f"  → テーブル名: {original_table} → {new_table}")
            print(f"  → カラム変換数: {columns_converted}")

        except Exception as e:
            print(f"  → エラー: {e}")
            conversion_stats['failed_count'] += 1
            conversion_stats['errors'].append({
                'file': yaml_file.name,
                'error': str(e)
            })

    # 変換レポートを生成
    print(f"\n変換レポートを生成中...")
    generate_conversion_report(conversion_stats, output_dir)

    print(f"\n=== 変換完了 ===")
    print(f"成功: {conversion_stats['success_count']}/{conversion_stats['total_files']}個")
    print(f"テーブル名変換: {conversion_stats['table_renamed']}個")
    print(f"カラム名変換: {conversion_stats['columns_renamed']}個")
    print(f"出力ディレクトリ: {output_dir}")
    print(f"レポート: {output_dir / 'conversion_report.md'}")
    print(f"\n注意: オリジナルファイルは変更されていません。")
    print(f"変換後のファイルは {output_dir} に新しいテーブル名で保存されています。")


if __name__ == '__main__':
    main()