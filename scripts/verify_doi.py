#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
論文DOI検証スクリプト
CrossRef APIを使用してDOIの有効性を検証する
"""

import requests
import json
import sys
import logging
from datetime import datetime
from pathlib import Path

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/doi_verification.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class DOIVerifier:
    """DOI検証クラス"""
    
    def __init__(self):
        self.crossref_api_url = "https://api.crossref.org/works/"
        self.verification_results = []
        
    def verify_doi(self, doi):
        """DOIの有効性を検証"""
        try:
            # DOIの正規化
            doi = doi.strip()
            if not doi:
                return {"valid": False, "error": "DOIが空です"}
            
            # DOI形式の基本的な検証
            if not doi.startswith('10.'):
                return {
                    "valid": False,
                    "doi": doi,
                    "error": "無効なDOI形式です（10.で始まる必要があります）",
                    "verified_at": datetime.now().isoformat()
                }
            
            # CrossRef APIにリクエスト（タイムアウト設定）
            try:
                response = requests.get(f"{self.crossref_api_url}{doi}", timeout=30)
            except requests.exceptions.Timeout:
                return {
                    "valid": False,
                    "doi": doi,
                    "error": "API タイムアウト（30秒）",
                    "verified_at": datetime.now().isoformat()
                }
            except requests.exceptions.ConnectionError:
                return {
                    "valid": False,
                    "doi": doi,
                    "error": "ネットワーク接続エラー",
                    "verified_at": datetime.now().isoformat()
                }
            except requests.exceptions.RequestException as e:
                return {
                    "valid": False,
                    "doi": doi,
                    "error": f"リクエストエラー: {str(e)}",
                    "verified_at": datetime.now().isoformat()
                }
            
            if response.status_code == 200:
                try:
                    data = response.json()
                except json.JSONDecodeError:
                    return {
                        "valid": False,
                        "doi": doi,
                        "error": "APIレスポンスが無効なJSON形式です",
                        "verified_at": datetime.now().isoformat()
                    }
                
                work = data.get('message', {})
                
                # 論文情報の抽出
                title = work.get('title', [''])[0] if work.get('title') else ''
                authors = work.get('author', [])
                published_date = work.get('published-print', {}).get('date-parts', [[]])[0]
                
                return {
                    "valid": True,
                    "doi": doi,
                    "title": title,
                    "authors": [author.get('given', '') + ' ' + author.get('family', '') for author in authors],
                    "published_date": published_date,
                    "url": work.get('URL', ''),
                    "type": work.get('type', ''),
                    "verified_at": datetime.now().isoformat()
                }
            else:
                return {
                    "valid": False,
                    "doi": doi,
                    "error": f"API エラー: {response.status_code}",
                    "verified_at": datetime.now().isoformat()
                }
                
        except Exception as e:
            return {
                "valid": False,
                "doi": doi,
                "error": f"検証エラー: {str(e)}",
                "verified_at": datetime.now().isoformat()
            }
    
    def verify_doi_list(self, doi_list):
        """DOIリストの一括検証"""
        results = []
        
        for doi in doi_list:
            logging.info(f"DOI検証中: {doi}")
            result = self.verify_doi(doi)
            results.append(result)
            
            if result["valid"]:
                logging.info(f"✅ 有効なDOI: {doi}")
                logging.info(f"   タイトル: {result.get('title', 'N/A')}")
            else:
                logging.warning(f"❌ 無効なDOI: {doi}")
                logging.warning(f"   エラー: {result.get('error', 'N/A')}")
        
        self.verification_results = results
        return results
    
    def save_results(self, output_file="doi_verification_results.json"):
        """検証結果をJSONファイルに保存"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.verification_results, f, indent=2, ensure_ascii=False)
            logging.info(f"✅ 検証結果を保存しました: {output_file}")
        except Exception as e:
            logging.error(f"❌ 結果保存エラー: {e}")
    
    def generate_report(self):
        """検証レポートの生成"""
        if not self.verification_results:
            logging.warning("検証結果がありません")
            return
        
        valid_count = sum(1 for result in self.verification_results if result["valid"])
        total_count = len(self.verification_results)
        
        logging.info(f"\n📊 DOI検証レポート:")
        logging.info(f"総数: {total_count}")
        logging.info(f"有効: {valid_count}")
        logging.info(f"無効: {total_count - valid_count}")
        logging.info(f"成功率: {(valid_count/total_count)*100:.1f}%" if total_count > 0 else "0%")

def main():
    """メイン関数"""
    verifier = DOIVerifier()
    
    # コマンドライン引数の処理
    if len(sys.argv) > 1:
        # 引数で指定されたDOIを検証
        doi = sys.argv[1]
        logging.info(f"🚀 DOI検証開始: {doi}")
        
        result = verifier.verify_doi(doi)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        if result["valid"]:
            logging.info(f"✅ 有効なDOI: {doi}")
            logging.info(f"   タイトル: {result.get('title', 'N/A')}")
        else:
            logging.warning(f"❌ 無効なDOI: {doi}")
            logging.warning(f"   エラー: {result.get('error', 'N/A')}")
    else:
        # テスト用DOIリスト
        test_dois = [
            "10.1038/nature12373",
            "10.1126/science.1234567",
            "10.1000/182",
            "invalid-doi-test"
        ]
        
        logging.info("🚀 DOI検証開始（テストモード）")
        
        # DOI検証実行
        results = verifier.verify_doi_list(test_dois)
        
        # 結果保存
        verifier.save_results()
        
        # レポート生成
        verifier.generate_report()
    
    logging.info("✅ DOI検証完了")

if __name__ == "__main__":
    main()
