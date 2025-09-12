#!/usr/bin/env python3
"""
Excel のテーブル設計をYAMLに変換するスクリプト

Input: tools/config/smds_poc/smds_dbdesign.xlsx
Output: tools/config/smds_poc/[テーブル名].yaml
"""

import pandas as pd
import yaml
import os
import sys
from pathlib import Path


def read_excel_sheets(excel_path):
    """Excelファイルから対象シートを読み込む"""
    # 全シート名を取得
    xls = pd.ExcelFile(excel_path)
    target_sheets = [sheet for sheet in xls.sheet_names 
                    if sheet not in ['templete', '入力シート', '入力規則']]
    
    return xls, target_sheets


def parse_table_sheet(xls, sheet_name):
    """各シートからテーブル定義を読み込む"""
    df = pd.read_excel(xls, sheet_name=sheet_name, header=None)
    
    # B1セル（インデックス0,1）= description, B2セル（インデックス1,1）= table_name
    description = df.iloc[0, 1] if not pd.isna(df.iloc[0, 1]) else ""
    table_name = df.iloc[1, 1] if not pd.isna(df.iloc[1, 1]) else sheet_name
    
    # 3行目（インデックス2）はヘッダー行のため、4行目（インデックス3）からカラム定義を読み込む
    # A:description, B:name/old_name, C:data_type, D:primary_key, E:nullable, F:未使用, G:comment
    columns_data = []
    
    # 3行目（インデックス2）がヘッダー行かどうか確認
    header_row = df.iloc[2] if len(df) > 2 else None
    start_row = 3 if header_row is not None and (
        str(header_row[1]).strip() in ['レコード名', 'name'] or 
        str(header_row[2]).strip() in ['タイプ', 'type']
    ) else 2
    
    for i in range(start_row, len(df)):  # ヘッダー行をスキップして開始
        row = df.iloc[i]
        
        # B列（name）が空の場合は終了
        if pd.isna(row[1]) or str(row[1]).strip() == '':
            break
            
        # ヘッダー行の値かどうか確認してスキップ
        if str(row[1]).strip() in ['レコード名', 'name']:
            continue
            
        # primary_keyの判定（D列が'○'の場合True）
        is_primary_key = str(row[3]).strip() == '○' if not pd.isna(row[3]) else False
        
        # nullableの判定（E列）
        nullable_val = row[4] if not pd.isna(row[4]) else True
        if isinstance(nullable_val, str):
            nullable = nullable_val.strip().lower() not in ['false', 'no', '×', 'x']
        else:
            nullable = bool(nullable_val)
        
        column = {
            'name': str(row[1]).strip(),
            'old_name': str(row[1]).strip(),  # name と同じ値をセット
            'description': str(row[0]).strip() if not pd.isna(row[0]) else '',
            'data_type': str(row[2]).strip() if not pd.isna(row[2]) else '',
            'primary_key': is_primary_key,
            'nullable': nullable,
            'comment': str(row[6]).strip() if not pd.isna(row[6]) and str(row[6]).strip() != 'nan' else None
        }
        
        columns_data.append(column)
    
    return {
        'table_name': str(table_name).strip(),
        'description': str(description).strip(),
        'columns': columns_data
    }


def create_yaml_structure(table_info):
    """YAML構造を作成"""
    yaml_data = {
        'metadata': {
            'description': 'テーブル定義書',
            'author': 'Claude Code',
            'history': [
                {
                    'version': '1.0.0',
                    'date': '2025-09-12',
                    'author': 'Claude Code',
                    'comment': 'Excel → YAML変換による初回作成'
                }
            ]
        },
        'table_name': table_info['table_name'],
        'description': table_info['description'],
        'columns': []
    }
    
    for col in table_info['columns']:
        column_data = {
            'name': col['name'],
            'old_name': col['old_name'],
            'description': col['description'],
            'data_type': col['data_type'],
            'primary_key': col['primary_key'],
            'nullable': col['nullable'],
            'comment': col['comment']
        }
        yaml_data['columns'].append(column_data)
    
    return yaml_data


def save_yaml(yaml_data, output_path):
    """YAMLファイルを保存"""
    # カスタムYAML表現設定
    class CustomDumper(yaml.SafeDumper):
        def write_line_break(self, data=None):
            super().write_line_break(data)
            if len(self.indents) == 1:
                super().write_line_break()

    # YAMLの出力設定
    yaml.add_representer(type(None), lambda dumper, value: dumper.represent_scalar('tag:yaml.org,2002:null', ''))
    
    with open(output_path, 'w', encoding='utf-8') as f:
        # ヘッダーコメント
        f.write('#- metadata -----------------------------------------------\n')
        
        # yamlデータを文字列として取得して手動で整形
        yaml_str = yaml.dump(yaml_data, 
                           default_flow_style=False, 
                           allow_unicode=True,
                           sort_keys=False,
                           indent=2)
        
        # セクション区切りを追加
        lines = yaml_str.split('\n')
        result_lines = []
        in_columns = False
        
        for i, line in enumerate(lines):
            if line.startswith('table_name:'):
                result_lines.append('\n#- tableinfo ----------------------------------------------')
            elif line.startswith('columns:'):
                result_lines.append('\n#- columns info -------------------------------------------')
                in_columns = True
            
            result_lines.append(line)
        
        f.write('\n'.join(result_lines))


def main():
    """メイン処理"""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    excel_path = project_root / 'tools/config/smds_poc/smds_dbdesign.xlsx'
    output_dir = project_root / 'tools/config/smds_poc'
    
    if not excel_path.exists():
        print(f"Error: {excel_path} が見つかりません")
        sys.exit(1)
    
    try:
        # Excelファイルを読み込み
        print(f"Excelファイルを読み込み中: {excel_path}")
        xls, target_sheets = read_excel_sheets(excel_path)
        
        print(f"変換対象シート: {target_sheets}")
        
        # 各シートを処理
        success_count = 0
        for sheet_name in target_sheets:
            print(f"\n処理中: {sheet_name}")
            
            try:
                # シートからテーブル定義を読み込み
                table_info = parse_table_sheet(xls, sheet_name)
                
                # YAML構造を作成
                yaml_data = create_yaml_structure(table_info)
                
                # 出力ファイル名
                table_name = table_info['table_name']
                output_file = output_dir / f"{table_name}.yaml"
                
                # YAMLファイルを保存
                save_yaml(yaml_data, output_file)
                
                print(f"  → 保存: {output_file}")
                print(f"  → テーブル名: {table_name}")
                print(f"  → カラム数: {len(table_info['columns'])}")
                success_count += 1
                
            except Exception as e:
                print(f"  → エラー: {sheet_name} の処理中にエラーが発生しました: {e}")
                continue
        
        print(f"\n変換完了: {success_count}/{len(target_sheets)}個のテーブル定義を変換しました")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()