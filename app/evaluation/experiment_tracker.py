"""
实验追踪器 - 管理评估实验和A/B测试
使用SQLite存储实验配置和结果
"""
import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent.parent))

from app.evaluation.config import EXPERIMENTS_DB_PATH


class ExperimentTracker:
    """实验追踪与对比系统"""
    
    def __init__(self, db_path: str = None):
        """
        初始化实验追踪器
        
        Args:
            db_path: SQLite数据库路径
        """
        self.db_path = db_path or EXPERIMENTS_DB_PATH
        self._init_database()
    
    def _init_database(self):
        """初始化数据库表结构"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 实验记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS experiments (
                experiment_id TEXT PRIMARY KEY,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                config_json TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'running'
            )
        ''')
        
        # 评估结果表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS evaluation_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                experiment_id TEXT NOT NULL,
                test_case_id TEXT NOT NULL,
                retrieval_metrics_json TEXT,
                generation_metrics_json TEXT,
                overall_score REAL,
                FOREIGN KEY (experiment_id) REFERENCES experiments(experiment_id)
            )
        ''')
        
        # 创建索引
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_experiment_id 
            ON evaluation_results(experiment_id)
        ''')
        
        conn.commit()
        conn.close()
    
    def create_experiment(
        self, 
        config: Dict, 
        description: str = ""
    ) -> str:
        """
        创建新实验记录
        
        Args:
            config: 实验配置字典
                例如: {
                    "chunk_size": 500,
                    "chunk_overlap": 50,
                    "retrieval_k": 5,
                    "embedding_model": "text-embedding-v3"
                }
            description: 实验描述
            
        Returns:
            实验ID
        """
        experiment_id = f"exp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            """INSERT INTO experiments (experiment_id, config_json, description, status) 
               VALUES (?, ?, ?, ?)""",
            (experiment_id, json.dumps(config), description, 'running')
        )
        
        conn.commit()
        conn.close()
        
        print(f"✅ 创建实验: {experiment_id}")
        return experiment_id
    
    def update_experiment_status(
        self, 
        experiment_id: str, 
        status: str
    ):
        """
        更新实验状态
        
        Args:
            experiment_id: 实验ID
            status: 状态 (running/completed/failed)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE experiments SET status = ? WHERE experiment_id = ?",
            (status, experiment_id)
        )
        
        conn.commit()
        conn.close()
    
    def save_result(
        self, 
        experiment_id: str, 
        test_case_id: str,
        retrieval_metrics: Dict,
        generation_metrics: Dict = None,
        overall_score: float = None
    ):
        """
        保存单个测试用例的评估结果
        
        Args:
            experiment_id: 实验ID
            test_case_id: 测试用例ID
            retrieval_metrics: 检索层指标
            generation_metrics: 生成层指标（可选）
            overall_score: 综合得分（可选）
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            """INSERT INTO evaluation_results 
               (experiment_id, test_case_id, retrieval_metrics_json, 
                generation_metrics_json, overall_score)
               VALUES (?, ?, ?, ?, ?)""",
            (
                experiment_id, 
                test_case_id,
                json.dumps(retrieval_metrics),
                json.dumps(generation_metrics) if generation_metrics else None,
                overall_score
            )
        )
        
        conn.commit()
        conn.close()
    
    def save_batch_results(
        self, 
        experiment_id: str,
        results: List[Dict]
    ):
        """
        批量保存评估结果
        
        Args:
            experiment_id: 实验ID
            results: 评估结果列表，每个元素包含：
                - test_case_id
                - retrieval_metrics
                - generation_metrics (可选)
                - overall_score (可选)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for result in results:
            cursor.execute(
                """INSERT INTO evaluation_results 
                   (experiment_id, test_case_id, retrieval_metrics_json, 
                    generation_metrics_json, overall_score)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    experiment_id,
                    result['test_case_id'],
                    json.dumps(result['retrieval_metrics']),
                    json.dumps(result.get('generation_metrics')),
                    result.get('overall_score')
                )
            )
        
        conn.commit()
        conn.close()
        
        print(f"✅ 保存 {len(results)} 条评估结果")
    
    def get_experiment(self, experiment_id: str) -> Optional[Dict]:
        """
        获取实验信息
        
        Args:
            experiment_id: 实验ID
            
        Returns:
            实验信息字典
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM experiments WHERE experiment_id = ?",
            (experiment_id,)
        )
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'experiment_id': row['experiment_id'],
                'timestamp': row['timestamp'],
                'config': json.loads(row['config_json']),
                'description': row['description'],
                'status': row['status']
            }
        
        return None
    
    def list_experiments(self, limit: int = 20) -> List[Dict]:
        """
        列出最近的实验
        
        Args:
            limit: 返回数量限制
            
        Returns:
            实验列表
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM experiments ORDER BY timestamp DESC LIMIT ?",
            (limit,)
        )
        
        rows = cursor.fetchall()
        conn.close()
        
        experiments = []
        for row in rows:
            experiments.append({
                'experiment_id': row['experiment_id'],
                'timestamp': row['timestamp'],
                'config': json.loads(row['config_json']),
                'description': row['description'],
                'status': row['status']
            })
        
        return experiments
    
    def get_aggregate_metrics(self, experiment_id: str) -> Dict:
        """
        获取实验的聚合指标
        
        Args:
            experiment_id: 实验ID
            
        Returns:
            聚合指标字典
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            """SELECT retrieval_metrics_json, generation_metrics_json, overall_score
               FROM evaluation_results
               WHERE experiment_id = ?""",
            (experiment_id,)
        )
        
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return {}
        
        # 聚合检索指标
        precision_list = []
        recall_list = []
        mrr_list = []
        ndcg_list = []
        overall_scores = []
        
        for row in rows:
            retrieval_metrics = json.loads(row[0])
            
            if 'precision@k' in retrieval_metrics:
                precision_list.append(retrieval_metrics['precision@k'])
            if 'recall@k' in retrieval_metrics:
                recall_list.append(retrieval_metrics['recall@k'])
            if 'mrr' in retrieval_metrics:
                mrr_list.append(retrieval_metrics['mrr'])
            if 'ndcg@k' in retrieval_metrics:
                ndcg_list.append(retrieval_metrics['ndcg@k'])
            
            if row[2] is not None:  # overall_score
                overall_scores.append(row[2])
        
        metrics = {
            'avg_precision': sum(precision_list) / len(precision_list) if precision_list else 0,
            'avg_recall': sum(recall_list) / len(recall_list) if recall_list else 0,
            'avg_mrr': sum(mrr_list) / len(mrr_list) if mrr_list else 0,
            'avg_ndcg': sum(ndcg_list) / len(ndcg_list) if ndcg_list else 0,
            'total_cases': len(rows)
        }
        
        if overall_scores:
            metrics['avg_overall_score'] = sum(overall_scores) / len(overall_scores)
        
        return metrics
    
    def compare_experiments(self, experiment_ids: List[str]) -> Dict:
        """
        对比多个实验的结果
        
        Args:
            experiment_ids: 实验ID列表
            
        Returns:
            对比结果字典
        """
        comparison = {}
        
        for exp_id in experiment_ids:
            experiment_info = self.get_experiment(exp_id)
            metrics = self.get_aggregate_metrics(exp_id)
            
            comparison[exp_id] = {
                'config': experiment_info['config'] if experiment_info else {},
                'metrics': metrics,
                'timestamp': experiment_info['timestamp'] if experiment_info else ''
            }
        
        # 计算相对提升（以第一个实验为基线）
        if len(experiment_ids) > 1:
            baseline_id = experiment_ids[0]
            baseline_metrics = comparison[baseline_id]['metrics']
            
            for exp_id in experiment_ids[1:]:
                exp_metrics = comparison[exp_id]['metrics']
                
                improvements = {}
                for metric in ['avg_precision', 'avg_recall', 'avg_mrr', 'avg_ndcg']:
                    if metric in baseline_metrics and metric in exp_metrics:
                        baseline_val = baseline_metrics[metric]
                        exp_val = exp_metrics[metric]
                        
                        if baseline_val > 0:
                            improvement = (exp_val - baseline_val) / baseline_val * 100
                            improvements[f'{metric}_improvement'] = improvement
                
                comparison[exp_id]['improvements'] = improvements
        
        return comparison
    
    def delete_experiment(self, experiment_id: str):
        """
        删除实验及其结果
        
        Args:
            experiment_id: 实验ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 删除评估结果
        cursor.execute(
            "DELETE FROM evaluation_results WHERE experiment_id = ?",
            (experiment_id,)
        )
        
        # 删除实验记录
        cursor.execute(
            "DELETE FROM experiments WHERE experiment_id = ?",
            (experiment_id,)
        )
        
        conn.commit()
        conn.close()
        
        print(f"✅ 已删除实验: {experiment_id}")
    
    def export_results(
        self, 
        experiment_id: str, 
        output_path: str
    ):
        """
        导出实验结果为JSON文件
        
        Args:
            experiment_id: 实验ID
            output_path: 输出文件路径
        """
        experiment_info = self.get_experiment(experiment_id)
        metrics = self.get_aggregate_metrics(experiment_id)
        
        export_data = {
            'experiment_id': experiment_id,
            'timestamp': experiment_info['timestamp'] if experiment_info else '',
            'config': experiment_info['config'] if experiment_info else {},
            'aggregate_metrics': metrics
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 结果已导出到: {output_path}")


if __name__ == "__main__":
    # 测试代码
    tracker = ExperimentTracker()
    
    # 创建示例实验
    config = {
        "chunk_size": 500,
        "chunk_overlap": 50,
        "retrieval_k": 5
    }
    
    exp_id = tracker.create_experiment(config, "测试实验")
    
    # 列出实验
    experiments = tracker.list_experiments()
    print(f"\n实验列表: {len(experiments)} 个实验")
    
    for exp in experiments:
        print(f"- {exp['experiment_id']}: {exp['description']}")
