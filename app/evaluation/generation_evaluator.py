"""
生成层评估器 - 基于LLM-as-Judge的答案质量评估
使用通义千问作为评判者，评估答案的忠实度、相关性和完整性
"""
import json
import re
from typing import Dict, List
from langchain_core.messages import HumanMessage

from app.core.rag_chain import RAGChain
from app.evaluation.config import (
    FAITHFULNESS_WEIGHT,
    RELEVANCE_WEIGHT,
    COMPLETENESS_WEIGHT
)


class GenerationEvaluator:
    """基于LLM的答案质量评估器"""
    
    def __init__(self, rag_chain: RAGChain = None):
        """
        初始化评估器
        
        Args:
            rag_chain: RAG链实例
        """
        self.rag_chain = rag_chain or RAGChain()
        self.llm = self.rag_chain.llm
    
    def evaluate_faithfulness(
        self, 
        question: str, 
        answer: str, 
        context: str
    ) -> Dict:
        """
        评估答案的忠实度（是否基于上下文，无幻觉）
        
        评分标准：
        1分 - 完全脱离上下文，纯幻觉
        2分 - 大部分内容无依据
        3分 - 部分基于上下文，有部分幻觉
        4分 - 基本基于上下文，少量幻觉
        5分 - 完全基于上下文，无幻觉
        
        Args:
            question: 用户问题
            answer: 生成的答案
            context: 参考上下文
            
        Returns:
            评估结果字典
        """
        prompt = f"""你是一个专业的RAG系统评估专家。请严格评估以下答案的忠实度。

【问题】
{question}

【参考上下文】
{context}

【生成的答案】
{answer}

【评估任务】
判断答案中的每个关键陈述是否都能在上下文中找到明确依据。

请按以下步骤分析：
1. 提取答案中的关键陈述（事实性声明）
2. 逐一验证每个陈述是否在上下文中出现或有明确支持
3. 标记 unsupported 的陈述
4. 给出1-5分的忠实度评分

评分标准：
- 5分：所有陈述都有明确依据，无幻觉
- 4分：绝大多数陈述有依据，极少数模糊
- 3分：约一半陈述有依据，存在明显幻觉
- 2分：大部分陈述无依据，严重幻觉
- 1分：完全脱离上下文，纯编造

请严格按照以下JSON格式输出（不要添加其他文字）：
{{
    "statements": [
        {{"statement": "陈述内容", "supported": true}},
        {{"statement": "另一个陈述", "supported": false}}
    ],
    "faithfulness_score": 4,
    "reasoning": "简要说明评分理由，指出主要的幻觉或不一致之处"
}}
"""
        
        try:
            response = self._invoke_llm(prompt)
            result = self._parse_json_response(response)
            
            # 验证结果格式
            if 'faithfulness_score' not in result:
                raise ValueError("响应中缺少faithfulness_score字段")
            
            return {
                'faithfulness_score': result['faithfulness_score'],
                'reasoning': result.get('reasoning', ''),
                'statements': result.get('statements', []),
                'unsupported_statements': [
                    s['statement'] for s in result.get('statements', [])
                    if not s.get('supported', True)
                ]
            }
        
        except Exception as e:
            print(f"⚠️ 忠实度评估失败: {str(e)}")
            return {
                'faithfulness_score': 0,
                'reasoning': f"评估失败: {str(e)}",
                'statements': [],
                'unsupported_statements': []
            }
    
    def evaluate_answer_relevance(
        self, 
        question: str, 
        answer: str
    ) -> Dict:
        """
        评估答案与问题的相关性
        
        评分标准：
        1分 - 完全无关，答非所问
        2分 - 轻微相关，但偏离核心问题
        3分 - 部分相关，回答了部分问题
        4分 - 高度相关，直接回答问题
        5分 - 完全相关，精准且完整地回答问题
        
        Args:
            question: 用户问题
            answer: 生成的答案
            
        Returns:
            评估结果字典
        """
        prompt = f"""请评估以下答案与问题的相关性。

【问题】
{question}

【答案】
{answer}

【评估维度】
1. 答案是否直接回应了问题的核心意图
2. 是否有答非所问或偏离主题的内容
3. 是否遗漏了问题的关键方面
4. 是否有不必要的冗余信息

评分标准：
- 5分：完美回答问题，无偏离，无遗漏
- 4分：很好地回答问题，略有不足
- 3分：部分回答问题，有明显遗漏或偏离
- 2分：勉强相关，大部分内容偏离
- 1分：完全不相关

请严格按照以下JSON格式输出：
{{
    "relevance_score": 4,
    "reasoning": "详细说明评分理由",
    "missing_aspects": ["遗漏的方面1", "遗漏的方面2"],
    "off_topic_content": ["偏离主题的内容1"]
}}
"""
        
        try:
            response = self._invoke_llm(prompt)
            result = self._parse_json_response(response)
            
            if 'relevance_score' not in result:
                raise ValueError("响应中缺少relevance_score字段")
            
            return {
                'relevance_score': result['relevance_score'],
                'reasoning': result.get('reasoning', ''),
                'missing_aspects': result.get('missing_aspects', []),
                'off_topic_content': result.get('off_topic_content', [])
            }
        
        except Exception as e:
            print(f"⚠️ 相关性评估失败: {str(e)}")
            return {
                'relevance_score': 0,
                'reasoning': f"评估失败: {str(e)}",
                'missing_aspects': [],
                'off_topic_content': []
            }
    
    def evaluate_completeness(
        self, 
        question: str, 
        answer: str, 
        expected_keywords: List[str]
    ) -> Dict:
        """
        评估答案的完整性（基于期望关键词覆盖率）
        
        Args:
            question: 用户问题
            answer: 生成的答案
            expected_keywords: 期望答案中包含的关键词列表
            
        Returns:
            评估结果字典
        """
        # 计算关键词匹配率
        matched_keywords = [
            kw for kw in expected_keywords 
            if kw.lower() in answer.lower()
        ]
        
        coverage = (
            len(matched_keywords) / len(expected_keywords) 
            if expected_keywords else 0
        )
        
        # 转换为1-5分
        if coverage >= 0.9:
            score = 5
        elif coverage >= 0.7:
            score = 4
        elif coverage >= 0.5:
            score = 3
        elif coverage >= 0.3:
            score = 2
        else:
            score = 1
        
        return {
            'completeness_score': score,
            'keyword_coverage': coverage,
            'matched_keywords': matched_keywords,
            'missing_keywords': [
                kw for kw in expected_keywords 
                if kw.lower() not in answer.lower()
            ],
            'total_keywords': len(expected_keywords)
        }
    
    def comprehensive_evaluate(
        self, 
        question: str, 
        answer: str, 
        context: str, 
        expected_keywords: List[str] = None
    ) -> Dict:
        """
        综合评估答案质量（三个维度）
        
        Args:
            question: 用户问题
            answer: 生成的答案
            context: 参考上下文
            expected_keywords: 期望关键词列表（可选）
            
        Returns:
            包含三个维度评估结果的字典
        """
        expected_keywords = expected_keywords or []
        
        # 并行评估三个维度（实际是串行，但可以优化为并行）
        faithfulness = self.evaluate_faithfulness(question, answer, context)
        relevance = self.evaluate_answer_relevance(question, answer)
        completeness = self.evaluate_completeness(
            question, answer, expected_keywords
        )
        
        # 计算综合得分（加权平均）
        overall_score = (
            faithfulness['faithfulness_score'] * FAITHFULNESS_WEIGHT +
            relevance['relevance_score'] * RELEVANCE_WEIGHT +
            completeness['completeness_score'] * COMPLETENESS_WEIGHT
        )
        
        return {
            'faithfulness': faithfulness,
            'relevance': relevance,
            'completeness': completeness,
            'overall_score': round(overall_score, 2),
            'weights': {
                'faithfulness': FAITHFULNESS_WEIGHT,
                'relevance': RELEVANCE_WEIGHT,
                'completeness': COMPLETENESS_WEIGHT
            }
        }
    
    def evaluate_rag_response(
        self,
        question: str,
        k: int = 5,
        expected_keywords: List[str] = None
    ) -> Dict:
        """
        完整的RAG响应评估流程
        
        Args:
            question: 用户问题
            k: 检索文档数量
            expected_keywords: 期望关键词
            
        Returns:
            包含检索和生成评估的完整结果
        """
        # 1. 执行RAG查询
        result = self.rag_chain.query(question, k=k)
        
        answer = result['answer']
        sources = result['sources']
        
        # 2. 构建上下文
        context = "\n\n".join([
            source['content'] for source in sources
        ])
        
        # 3. 评估答案质量
        evaluation = self.comprehensive_evaluate(
            question, answer, context, expected_keywords
        )
        
        # 4. 整合结果
        return {
            'question': question,
            'answer': answer,
            'sources_count': len(sources),
            'evaluation': evaluation,
            'sources': sources
        }
    
    def _invoke_llm(self, prompt: str) -> str:
        """
        调用LLM生成响应
        
        Args:
            prompt: 提示词
            
        Returns:
            LLM响应文本
        """
        if self.llm is None:
            raise ValueError("LLM未初始化")
        
        try:
            # 兼容ChatModel和传统LLM
            from app.core.rag_chain import USE_CHAT_MODEL
            
            if USE_CHAT_MODEL:
                response = self.llm.invoke([HumanMessage(content=prompt)])
                return response.content if hasattr(response, 'content') else str(response)
            else:
                return self.llm.invoke(prompt)
        
        except Exception as e:
            raise Exception(f"LLM调用失败: {str(e)}")
    
    def _parse_json_response(self, response: str) -> Dict:
        """
        从LLM响应中解析JSON
        
        Args:
            response: LLM响应文本
            
        Returns:
            解析后的字典
        """
        # 尝试直接解析
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass
        
        # 尝试提取JSON代码块
        json_pattern = r'```json\s*(.*?)\s*```'
        match = re.search(json_pattern, response, re.DOTALL)
        
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
        
        # 尝试查找花括号包裹的内容
        brace_pattern = r'\{.*\}'
        match = re.search(brace_pattern, response, re.DOTALL)
        
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
        
        # 如果都失败，抛出异常
        raise ValueError(f"无法解析JSON响应: {response[:200]}")
    
    def batch_evaluate(
        self,
        test_cases_with_answers: List[Dict],
        verbose: bool = True
    ) -> List[Dict]:
        """
        批量评估多个问答对
        
        Args:
            test_cases_with_answers: 包含问题和答案的测试用例列表
                格式: [
                    {
                        'question': '...',
                        'answer': '...',
                        'context': '...',
                        'expected_keywords': [...]
                    },
                    ...
                ]
            verbose: 是否显示进度
            
        Returns:
            评估结果列表
        """
        results = []
        total = len(test_cases_with_answers)
        
        for i, test_case in enumerate(test_cases_with_answers):
            if verbose:
                print(f"评估进度: {i+1}/{total}")
            
            try:
                evaluation = self.comprehensive_evaluate(
                    question=test_case['question'],
                    answer=test_case['answer'],
                    context=test_case['context'],
                    expected_keywords=test_case.get('expected_keywords', [])
                )
                
                results.append({
                    'test_index': i,
                    'question': test_case['question'],
                    'evaluation': evaluation
                })
            
            except Exception as e:
                print(f"⚠️ 评估失败 (case {i}): {str(e)}")
                continue
        
        return results


if __name__ == "__main__":
    # 测试代码
    print("初始化生成评估器...")
    evaluator = GenerationEvaluator()
    
    # 示例评估
    question = "RAG系统使用的是什么向量数据库？"
    
    print(f"\n评估问题: {question}")
    result = evaluator.evaluate_rag_response(
        question,
        k=5,
        expected_keywords=["ChromaDB", "向量"]
    )
    
    eval_result = result['evaluation']
    
    print(f"\n===== 评估结果 =====")
    print(f"忠实度: {eval_result['faithfulness']['faithfulness_score']}/5")
    print(f"相关性: {eval_result['relevance']['relevance_score']}/5")
    print(f"完整性: {eval_result['completeness']['completeness_score']}/5")
    print(f"综合得分: {eval_result['overall_score']}/5")
    print(f"\n答案:\n{result['answer']}")
