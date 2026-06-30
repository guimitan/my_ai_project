"""
评估运行器 - 执行完整的评估流程
整合检索评估和生成评估，保存结果到实验追踪器
"""
from typing import List, Dict

from app.evaluation.dataset_manager import TestDatasetManager, TestCase
from app.evaluation.retrieval_evaluator import RetrievalEvaluator
from app.evaluation.generation_evaluator import GenerationEvaluator
from app.evaluation.experiment_tracker import ExperimentTracker
from app.core.rag_chain import RAGChain


class EvaluationRunner:
    """评估流程运行器"""
    
    def __init__(
        self,
        dataset_name: str = "test_cases",
        rag_chain: RAGChain = None
    ):
        """
        初始化评估运行器
        
        Args:
            dataset_name: 数据集名称
            rag_chain: RAG链实例
        """
        self.dataset_manager = TestDatasetManager(dataset_name)
        self.rag_chain = rag_chain or RAGChain()
        self.retrieval_evaluator = RetrievalEvaluator(self.rag_chain)
        self.generation_evaluator = GenerationEvaluator(self.rag_chain)
        self.experiment_tracker = ExperimentTracker()
    
    def run_full_evaluation(
        self,
        experiment_config: Dict = None,
        experiment_description: str = "",
        k: int = 5,
        evaluate_generation: bool = True,
        verbose: bool = True
    ) -> Dict:
        """
        运行完整的评估流程（检索 + 生成）
        
        Args:
            experiment_config: 实验配置
            experiment_description: 实验描述
            k: 检索文档数量
            evaluate_generation: 是否评估生成质量
            verbose: 是否显示详细进度
            
        Returns:
            完整的评估结果
        """
        # 1. 创建实验记录
        if experiment_config is None:
            experiment_config = {
                "retrieval_k": k,
                "evaluate_generation": evaluate_generation
            }
        
        experiment_id = self.experiment_tracker.create_experiment(
            config=experiment_config,
            description=experiment_description
        )
        
        if verbose:
            print(f"\n{'='*60}")
            print(f"开始评估实验: {experiment_id}")
            print(f"{'='*60}\n")
        
        # 2. 加载测试用例
        test_cases = self.dataset_manager.get_all_test_cases()
        
        if not test_cases:
            print("⚠️ 数据集中没有测试用例")
            return {}
        
        if verbose:
            print(f"加载了 {len(test_cases)} 个测试用例\n")
        
        # 3. 执行检索评估
        if verbose:
            print("【步骤1】执行检索层评估...")
        
        retrieval_results = self.retrieval_evaluator.evaluate_batch(
            test_cases, k=k, verbose=verbose
        )
        
        # 4. 执行生成评估（可选）
        generation_results = []
        
        if evaluate_generation:
            if verbose:
                print("\n【步骤2】执行生成层评估...")
            
            for i, test_case in enumerate(test_cases):
                if verbose:
                    print(f"评估生成质量: {i+1}/{len(test_cases)}")
                
                try:
                    # 执行RAG查询
                    rag_result = self.rag_chain.query(test_case.question, k=k)
                    
                    # 构建上下文
                    context = "\n\n".join([
                        source['content'] for source in rag_result['sources']
                    ])
                    
                    # 评估答案质量
                    evaluation = self.generation_evaluator.comprehensive_evaluate(
                        question=test_case.question,
                        answer=rag_result['answer'],
                        context=context,
                        expected_keywords=test_case.expected_keywords
                    )
                    
                    generation_results.append({
                        'test_case_id': test_case.test_id,
                        'evaluation': evaluation
                    })
                
                except Exception as e:
                    print(f"⚠️ 生成评估失败 {test_case.test_id}: {str(e)}")
                    continue
        
        # 5. 整合结果并保存
        if verbose:
            print("\n【步骤3】保存评估结果...")
        
        all_results = []
        
        for i, retrieval_result in enumerate(retrieval_results['individual_results']):
            test_case_id = retrieval_result['test_id']
            
            # 查找对应的生成评估结果
            gen_result = None
            for gr in generation_results:
                if gr['test_case_id'] == test_case_id:
                    gen_result = gr
                    break
            
            # 计算综合得分（如果有生成评估）
            overall_score = None
            if gen_result:
                overall_score = gen_result['evaluation']['overall_score']
            
            # 保存到实验追踪器
            self.experiment_tracker.save_result(
                experiment_id=experiment_id,
                test_case_id=test_case_id,
                retrieval_metrics=retrieval_result,
                generation_metrics=gen_result['evaluation'] if gen_result else None,
                overall_score=overall_score
            )
            
            all_results.append({
                'test_case_id': test_case_id,
                'retrieval_metrics': retrieval_result,
                'generation_metrics': gen_result['evaluation'] if gen_result else None,
                'overall_score': overall_score
            })
        
        # 6. 更新实验状态
        self.experiment_tracker.update_experiment_status(experiment_id, 'completed')
        
        # 7. 生成报告
        if verbose:
            print("\n" + "="*60)
            print("评估完成！")
            print("="*60)
            
            # 打印检索指标报告
            print(self.retrieval_evaluator.generate_report(retrieval_results))
            
            # 如果有生成评估，打印生成指标
            if generation_results:
                self._print_generation_report(generation_results)
        
        return {
            'experiment_id': experiment_id,
            'retrieval_results': retrieval_results,
            'generation_results': generation_results,
            'all_results': all_results
        }
    
    def run_retrieval_only(
        self,
        k: int = 5,
        verbose: bool = True
    ) -> Dict:
        """
        仅运行检索评估（快速模式）
        
        Args:
            k: 检索文档数量
            verbose: 是否显示进度
            
        Returns:
            检索评估结果
        """
        test_cases = self.dataset_manager.get_all_test_cases()
        
        if verbose:
            print(f"执行检索评估 ({len(test_cases)} 个测试用例)...")
        
        results = self.retrieval_evaluator.evaluate_batch(test_cases, k=k, verbose=verbose)
        
        # 生成报告
        print(self.retrieval_evaluator.generate_report(results))
        
        return results
    
    def _print_generation_report(self, generation_results: List[Dict]):
        """打印生成评估报告"""
        if not generation_results:
            return
        
        # 计算平均分
        faithfulness_scores = [
            gr['evaluation']['faithfulness']['faithfulness_score']
            for gr in generation_results
        ]
        relevance_scores = [
            gr['evaluation']['relevance']['relevance_score']
            for gr in generation_results
        ]
        completeness_scores = [
            gr['evaluation']['completeness']['completeness_score']
            for gr in generation_results
        ]
        overall_scores = [
            gr['evaluation']['overall_score']
            for gr in generation_results
        ]
        
        print("\n===== 生成质量评估报告 =====")
        print(f"评估样本数: {len(generation_results)}")
        print(f"\n忠实度 (Faithfulness): {sum(faithfulness_scores)/len(faithfulness_scores):.2f}/5")
        print(f"相关性 (Relevance):   {sum(relevance_scores)/len(relevance_scores):.2f}/5")
        print(f"完整性 (Completeness): {sum(completeness_scores)/len(completeness_scores):.2f}/5")
        print(f"\n综合得分: {sum(overall_scores)/len(overall_scores):.2f}/5")
        print("="*40)


def main():
    """主函数 - 命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='RAG检索质量评估系统')
    parser.add_argument(
        '--dataset',
        type=str,
        default='test_cases',
        help='数据集名称'
    )
    parser.add_argument(
        '--k',
        type=int,
        default=5,
        help='检索文档数量'
    )
    parser.add_argument(
        '--mode',
        type=str,
        choices=['full', 'retrieval'],
        default='full',
        help='评估模式: full(完整评估) 或 retrieval(仅检索)'
    )
    parser.add_argument(
        '--description',
        type=str,
        default='',
        help='实验描述'
    )
    
    args = parser.parse_args()
    
    # 创建评估运行器
    runner = EvaluationRunner(dataset_name=args.dataset)
    
    # 运行评估
    if args.mode == 'full':
        runner.run_full_evaluation(
            experiment_description=args.description,
            k=args.k,
            evaluate_generation=True,
            verbose=True
        )
    else:
        runner.run_retrieval_only(k=args.k, verbose=True)


if __name__ == "__main__":
    main()
