"""
检索层评估器
实现Precision、Recall、MRR、NDCG等经典信息检索指标
"""
import numpy as np
from typing import List, Dict, Set
from langchain_core.documents import Document

from app.core.rag_chain import RAGChain
from app.evaluation.dataset_manager import TestCase


class RetrievalEvaluator:
    """检索质量评估器"""
    
    def __init__(self, rag_chain: RAGChain = None):
        """
        初始化评估器
        
        Args:
            rag_chain: RAG链实例，如果为None则自动创建
        """
        self.rag_chain = rag_chain or RAGChain()
    
    def evaluate_single_case(
        self, 
        test_case: TestCase, 
        k: int = 5
    ) -> Dict:
        """
        评估单个测试用例的检索质量
        
        Args:
            test_case: 测试用例
            k: 检索返回的文档数量
            
        Returns:
            评估结果字典
        """
        question = test_case.question
        relevant_ids = set(test_case.relevant_doc_ids)
        
        # 执行检索
        retrieved_docs = self.rag_chain.retrieve_context(question, k=k)
        
        # 提取检索到的文档ID（从metadata中获取）
        retrieved_ids = []
        for doc in retrieved_docs:
            doc_id = doc.metadata.get('doc_id') or doc.metadata.get('source', '')
            retrieved_ids.append(doc_id)
        
        # 计算各项指标
        precision = self._calculate_precision(retrieved_ids, relevant_ids, k)
        recall = self._calculate_recall(retrieved_ids, relevant_ids)
        mrr = self._calculate_mrr(retrieved_ids, relevant_ids)
        ndcg = self._calculate_ndcg(retrieved_ids, relevant_ids, k)
        
        # 收集相似度分数（如果有）
        similarity_scores = []
        for doc in retrieved_docs:
            score = doc.metadata.get('score', 0)
            similarity_scores.append(score)
        
        return {
            'test_id': test_case.test_id,
            'question': question,
            'category': test_case.category,
            'difficulty': test_case.difficulty,
            'precision@k': precision,
            'recall@k': recall,
            'mrr': mrr,
            'ndcg@k': ndcg,
            'similarity_scores': similarity_scores,
            'retrieved_count': len(retrieved_ids),
            'relevant_found': len(set(retrieved_ids) & relevant_ids),
            'total_relevant': len(relevant_ids)
        }
    
    def evaluate_batch(
        self, 
        test_cases: List[TestCase], 
        k: int = 5,
        verbose: bool = True
    ) -> Dict:
        """
        批量评估测试集
        
        Args:
            test_cases: 测试用例列表
            k: 检索返回的文档数量
            verbose: 是否显示进度
            
        Returns:
            包含个体结果和聚合指标的字典
        """
        results = []
        total = len(test_cases)
        
        for i, test_case in enumerate(test_cases):
            if verbose:
                print(f"评估进度: {i+1}/{total} - {test_case.test_id}")
            
            try:
                result = self.evaluate_single_case(test_case, k)
                results.append(result)
            except Exception as e:
                print(f"⚠️ 评估失败 {test_case.test_id}: {str(e)}")
                continue
        
        # 计算聚合指标
        aggregate_metrics = self._aggregate_metrics(results)
        
        return {
            'individual_results': results,
            'aggregate_metrics': aggregate_metrics,
            'total_evaluated': len(results)
        }
    
    def _calculate_precision(
        self, 
        retrieved_ids: List[str], 
        relevant_ids: Set[str], 
        k: int
    ) -> float:
        """
        计算Precision@K
        
        Precision@K = (前K个结果中的相关文档数) / K
        """
        if k == 0:
            return 0.0
        
        retrieved_at_k = retrieved_ids[:k]
        relevant_retrieved = len(set(retrieved_at_k) & relevant_ids)
        
        return relevant_retrieved / k
    
    def _calculate_recall(
        self, 
        retrieved_ids: List[str], 
        relevant_ids: Set[str]
    ) -> float:
        """
        计算Recall@K
        
        Recall@K = (召回的相关文档数) / (总相关文档数)
        """
        if len(relevant_ids) == 0:
            return 0.0
        
        relevant_retrieved = len(set(retrieved_ids) & relevant_ids)
        
        return relevant_retrieved / len(relevant_ids)
    
    def _calculate_mrr(
        self, 
        retrieved_ids: List[str], 
        relevant_ids: Set[str]
    ) -> float:
        """
        计算MRR (Mean Reciprocal Rank)
        
        MRR = 1 / (第一个相关文档的排名位置)
        """
        for i, doc_id in enumerate(retrieved_ids):
            if doc_id in relevant_ids:
                return 1.0 / (i + 1)
        
        return 0.0
    
    def _calculate_ndcg(
        self, 
        retrieved_ids: List[str], 
        relevant_ids: Set[str], 
        k: int
    ) -> float:
        """
        计算NDCG@K (Normalized Discounted Cumulative Gain)
        
        NDCG@K = DCG@K / IDCG@K
        
        DCG@K = sum(rel_i / log2(i+2)) for i in 0..K-1
        IDCG@K = 理想情况下的DCG@K
        """
        # 计算DCG
        dcg = 0.0
        for i, doc_id in enumerate(retrieved_ids[:k]):
            rel = 1 if doc_id in relevant_ids else 0
            dcg += rel / np.log2(i + 2)  # i+2 because i starts from 0
        
        # 计算IDCG（理想情况下的DCG）
        ideal_rels = sorted(
            [1 if doc_id in relevant_ids else 0 for doc_id in retrieved_ids],
            reverse=True
        )[:k]
        
        idcg = sum(rel / np.log2(i + 2) for i, rel in enumerate(ideal_rels))
        
        return dcg / idcg if idcg > 0 else 0.0
    
    def _aggregate_metrics(self, results: List[Dict]) -> Dict:
        """
        聚合多个测试用例的评估结果
        
        Args:
            results: 个体评估结果列表
            
        Returns:
            聚合指标字典
        """
        if not results:
            return {
                'avg_precision': 0.0,
                'avg_recall': 0.0,
                'avg_mrr': 0.0,
                'avg_ndcg': 0.0,
                'total_cases': 0
            }
        
        return {
            'avg_precision': np.mean([r['precision@k'] for r in results]),
            'avg_recall': np.mean([r['recall@k'] for r in results]),
            'avg_mrr': np.mean([r['mrr'] for r in results]),
            'avg_ndcg': np.mean([r['ndcg@k'] for r in results]),
            'std_precision': np.std([r['precision@k'] for r in results]),
            'std_recall': np.std([r['recall@k'] for r in results]),
            'std_mrr': np.std([r['mrr'] for r in results]),
            'std_ndcg': np.std([r['ndcg@k'] for r in results]),
            'total_cases': len(results)
        }
    
    def analyze_similarity_distribution(
        self, 
        results: List[Dict]
    ) -> Dict:
        """
        分析相似度分数分布
        
        Args:
            results: 评估结果列表
            
        Returns:
            分布统计信息
        """
        all_scores = []
        for r in results:
            all_scores.extend(r['similarity_scores'])
        
        if not all_scores:
            return {}
        
        scores_array = np.array(all_scores)
        
        return {
            'mean': float(np.mean(scores_array)),
            'std': float(np.std(scores_array)),
            'min': float(np.min(scores_array)),
            'max': float(np.max(scores_array)),
            'median': float(np.median(scores_array)),
            'q1': float(np.percentile(scores_array, 25)),
            'q3': float(np.percentile(scores_array, 75)),
            'total_scores': len(all_scores)
        }
    
    def find_low_performing_cases(
        self, 
        results: List[Dict], 
        metric: str = 'precision@k',
        threshold: float = 0.5,
        top_n: int = 10
    ) -> List[Dict]:
        """
        找出表现较差的测试用例
        
        Args:
            results: 评估结果列表
            metric: 评估指标名称
            threshold: 阈值
            top_n: 返回的数量
            
        Returns:
            低分案例列表
        """
        low_performing = [
            r for r in results 
            if r[metric] < threshold
        ]
        
        # 按指标排序
        low_performing.sort(key=lambda x: x[metric])
        
        return low_performing[:top_n]
    
    def generate_report(self, evaluation_result: Dict) -> str:
        """
        生成评估报告文本
        
        Args:
            evaluation_result: 评估结果字典
            
        Returns:
            格式化的报告文本
        """
        metrics = evaluation_result['aggregate_metrics']
        total = metrics['total_cases']
        
        report = f"""
{'='*60}
           检索质量评估报告
{'='*60}

测试用例总数: {total}

【核心指标】
• Precision@5: {metrics['avg_precision']:.2%} (±{metrics['std_precision']:.2%})
• Recall@5:    {metrics['avg_recall']:.2%} (±{metrics['std_recall']:.2%})
• MRR:         {metrics['avg_mrr']:.3f} (±{metrics['std_mrr']:.3f})
• NDCG@5:      {metrics['avg_ndcg']:.3f} (±{metrics['std_ndcg']:.3f})

【说明】
- Precision@5: 前5个检索结果中相关文档的比例
- Recall@5:    所有相关文档中被召回的比例
- MRR:         第一个相关文档排名的倒数均值
- NDCG@5:      考虑排名位置的归一化折损累计增益

{'='*60}
"""
        
        return report


if __name__ == "__main__":
    # 测试代码
    from app.evaluation.dataset_manager import TestDatasetManager
    
    print("初始化检索评估器...")
    evaluator = RetrievalEvaluator()
    
    print("\n加载测试数据集...")
    dataset_manager = TestDatasetManager("test_cases")
    test_cases = dataset_manager.get_all_test_cases()
    
    if test_cases:
        print(f"\n开始评估 {len(test_cases)} 个测试用例...")
        results = evaluator.evaluate_batch(test_cases, k=5)
        
        # 生成报告
        report = evaluator.generate_report(results)
        print(report)
    else:
        print("⚠️ 数据集中没有测试用例")
