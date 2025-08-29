#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Scholar検索自動化スクリプト
論文検索とメタデータ抽出を自動化
"""

import json
import sys
import logging
from datetime import datetime
from pathlib import Path

# scholarlyライブラリのインポート（インストールが必要）
try:
    from scholarly import scholarly
    SCHOLARLY_AVAILABLE = True
except ImportError:
    SCHOLARLY_AVAILABLE = False
    logging.warning("scholarlyライブラリがインストールされていません。pip install scholarly を実行してください。")

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/scholar_search.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class ScholarSearcher:
    """Google Scholar検索クラス"""
    
    def __init__(self):
        self.search_results = []
        
    def search_papers(self, query, count=5):
        """論文検索を実行"""
        if not SCHOLARLY_AVAILABLE:
            return {
                "error": "scholarlyライブラリが利用できません",
                "install_command": "pip install scholarly"
            }
        
        try:
            results = []
            search = scholarly.search_pubs(query)
            
            for i in range(count):
                try:
                    paper = next(search)
                    paper_data = {
                        "title": paper.get("bib", {}).get("title"),
                        "authors": paper.get("bib", {}).get("author"),
                        "year": paper.get("bib", {}).get("pub_year"),
                        "url": paper.get("pub_url"),
                        "abstract": paper.get("bib", {}).get("abstract"),
                        "citations": paper.get("num_citations", 0),
                        "venue": paper.get("bib", {}).get("venue"),
                        "search_rank": i + 1
                    }
                    results.append(paper_data)
                    
                    logging.info(f"📄 論文{i+1}: {paper_data['title']}")
                    logging.info(f"   著者: {', '.join(paper_data['authors']) if paper_data['authors'] else 'N/A'}")
                    logging.info(f"   年: {paper_data['year']}")
                    logging.info(f"   引用数: {paper_data['citations']}")
                    
                except StopIteration:
                    break
                except Exception as e:
                    logging.warning(f"論文{i+1}の処理でエラー: {e}")
                    continue
            
            self.search_results = results
            return {
                "success": True,
                "query": query,
                "count": len(results),
                "results": results,
                "searched_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logging.error(f"検索エラー: {e}")
            return {
                "success": False,
                "error": str(e),
                "query": query,
                "searched_at": datetime.now().isoformat()
            }
    
    def save_results(self, output_file="scholar_search_results.json"):
        """検索結果をJSONファイルに保存"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.search_results, f, indent=2, ensure_ascii=False)
            logging.info(f"✅ 検索結果を保存しました: {output_file}")
        except Exception as e:
            logging.error(f"❌ 結果保存エラー: {e}")
    
    def generate_report(self):
        """検索レポートの生成"""
        if not self.search_results:
            logging.warning("検索結果がありません")
            return
        
        total_citations = sum(result.get('citations', 0) for result in self.search_results)
        avg_citations = total_citations / len(self.search_results) if self.search_results else 0
        
        logging.info(f"\n📊 Scholar検索レポート:")
        logging.info(f"検索結果数: {len(self.search_results)}")
        logging.info(f"総引用数: {total_citations}")
        logging.info(f"平均引用数: {avg_citations:.1f}")
        
        # 引用数の多い論文を表示
        top_papers = sorted(self.search_results, key=lambda x: x.get('citations', 0), reverse=True)[:3]
        logging.info(f"\n🏆 高引用論文TOP3:")
        for i, paper in enumerate(top_papers, 1):
            logging.info(f"{i}. {paper['title']} ({paper.get('citations', 0)}引用)")

def main():
    """メイン関数"""
    searcher = ScholarSearcher()
    
    # コマンドライン引数の処理
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        # デフォルトクエリ
        query = "vocal tone persuasion psychology"
    
    logging.info(f"🚀 Scholar検索開始: {query}")
    
    # 検索実行
    result = searcher.search_papers(query, count=5)
    
    if result.get("success"):
        # 結果保存
        searcher.save_results()
        
        # レポート生成
        searcher.generate_report()
        
        logging.info("✅ Scholar検索完了")
    else:
        logging.error(f"❌ 検索失敗: {result.get('error')}")

if __name__ == "__main__":
    main()
