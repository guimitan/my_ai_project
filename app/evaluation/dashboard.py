"""
检索质量评估系统 - Streamlit可视化仪表板
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from app.evaluation.dataset_manager import TestDatasetManager
from app.evaluation.experiment_tracker import ExperimentTracker


# 页面配置
st.set_page_config(
    page_title="RAG检索质量评估系统",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: bold;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
</style>
""", unsafe_allow_html=True)


def load_experiment_data(experiment_id: str):
    """加载实验数据"""
    tracker = ExperimentTracker()
    
    experiment_info = tracker.get_experiment(experiment_id)
    metrics = tracker.get_aggregate_metrics(experiment_id)
    
    return experiment_info, metrics


def show_overview_tab(selected_experiments):
    """概览面板"""
    st.subheader("📈 核心指标概览")
    
    if not selected_experiments:
        st.warning("请先在侧边栏选择实验")
        return
    
    # 加载最新实验的数据
    latest_exp = selected_experiments[-1]
    experiment_info, metrics = load_experiment_data(latest_exp)
    
    if not metrics:
        st.info("该实验暂无评估数据")
        return
    
    # KPI卡片
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Precision@5",
            value=f"{metrics.get('avg_precision', 0):.2%}",
            delta=None
        )
    
    with col2:
        st.metric(
            label="Recall@5",
            value=f"{metrics.get('avg_recall', 0):.2%}",
            delta=None
        )
    
    with col3:
        st.metric(
            label="MRR",
            value=f"{metrics.get('avg_mrr', 0):.3f}",
            delta=None
        )
    
    with col4:
        st.metric(
            label="NDCG@5",
            value=f"{metrics.get('avg_ndcg', 0):.3f}",
            delta=None
        )
    
    st.divider()
    
    # 如果有综合得分，显示生成质量指标
    if 'avg_overall_score' in metrics:
        st.subheader("💬 生成质量指标")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric(
                label="答案综合得分",
                value=f"{metrics['avg_overall_score']:.2f}/5.0"
            )
        
        with col2:
            st.metric(
                label="评估样本数",
                value=metrics.get('total_cases', 0)
            )
    
    # 实验配置信息
    st.divider()
    st.subheader("⚙️ 实验配置")
    
    if experiment_info:
        config = experiment_info.get('config', {})
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write(f"**检索数量 (k):** {config.get('retrieval_k', 'N/A')}")
        
        with col2:
            st.write(f"**文本块大小:** {config.get('chunk_size', 'N/A')}")
        
        with col3:
            st.write(f"**重叠大小:** {config.get('chunk_overlap', 'N/A')}")
        
        st.write(f"**描述:** {experiment_info.get('description', '无')}")
        st.write(f"**时间:** {experiment_info.get('timestamp', 'N/A')}")


def show_retrieval_analysis_tab(selected_experiments):
    """检索质量分析"""
    st.subheader("🔍 检索质量详细分析")
    
    if not selected_experiments:
        st.warning("请先选择实验")
        return
    
    st.info("详细的检索指标分布分析功能正在开发中...\n\n当前版本提供基础指标查看，完整可视化将在下一版本更新。")
    
    # 显示各实验的聚合指标对比
    if len(selected_experiments) > 1:
        st.subheader("多实验对比")
        
        tracker = ExperimentTracker()
        comparison = tracker.compare_experiments(selected_experiments)
        
        # 构建对比表格
        data = []
        for exp_id, exp_data in comparison.items():
            metrics = exp_data['metrics']
            data.append({
                '实验ID': exp_id,
                'Precision': f"{metrics.get('avg_precision', 0):.2%}",
                'Recall': f"{metrics.get('avg_recall', 0):.2%}",
                'MRR': f"{metrics.get('avg_mrr', 0):.3f}",
                'NDCG': f"{metrics.get('avg_ndcg', 0):.3f}"
            })
        
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)


def show_generation_analysis_tab(selected_experiments):
    """生成质量分析"""
    st.subheader("💬 答案质量分析")
    
    if not selected_experiments:
        st.warning("请先选择实验")
        return
    
    st.info("LLM-as-Judge评估结果可视化功能正在开发中...\n\n当前版本支持在完整评估模式下查看综合得分。")


def show_experiment_comparison_tab(selected_experiments):
    """实验对比视图"""
    st.subheader("⚖️ 实验对比分析")
    
    if len(selected_experiments) < 2:
        st.info("请选择至少两个实验进行对比")
        return
    
    tracker = ExperimentTracker()
    comparison = tracker.compare_experiments(selected_experiments)
    
    # 实验配置对比
    st.write("**实验配置对比**")
    
    config_data = []
    for exp_id, exp_data in comparison.items():
        config = exp_data['config']
        config_data.append({
            '实验ID': exp_id,
            '检索数量 (k)': config.get('retrieval_k', 'N/A'),
            '文本块大小': config.get('chunk_size', 'N/A'),
            '重叠大小': config.get('chunk_overlap', 'N/A'),
            '时间': exp_data.get('timestamp', '')[:16]
        })
    
    config_df = pd.DataFrame(config_data)
    st.dataframe(config_df, use_container_width=True)
    
    st.divider()
    
    # 评估结果对比
    st.write("**评估结果对比**")
    
    metrics_data = []
    for exp_id, exp_data in comparison.items():
        metrics = exp_data['metrics']
        row = {
            '实验ID': exp_id,
            'Precision': f"{metrics.get('avg_precision', 0):.2%}",
            'Recall': f"{metrics.get('avg_recall', 0):.2%}",
            'MRR': f"{metrics.get('avg_mrr', 0):.3f}",
            'NDCG': f"{metrics.get('avg_ndcg', 0):.3f}"
        }
        
        if 'avg_overall_score' in metrics:
            row['综合得分'] = f"{metrics['avg_overall_score']:.2f}"
        
        metrics_data.append(row)
    
    metrics_df = pd.DataFrame(metrics_data)
    st.dataframe(metrics_df, use_container_width=True)
    
    st.divider()
    
    # 柱状图对比
    st.write("**指标可视化对比**")
    
    # 准备绘图数据
    plot_data = []
    for exp_id, exp_data in comparison.items():
        metrics = exp_data['metrics']
        plot_data.append({
            'experiment': exp_id,
            'metric': 'Precision',
            'value': metrics.get('avg_precision', 0) * 100  # 转换为百分比
        })
        plot_data.append({
            'experiment': exp_id,
            'metric': 'Recall',
            'value': metrics.get('avg_recall', 0) * 100
        })
        plot_data.append({
            'experiment': exp_id,
            'metric': 'MRR',
            'value': metrics.get('avg_mrr', 0)
        })
        plot_data.append({
            'experiment': exp_id,
            'metric': 'NDCG',
            'value': metrics.get('avg_ndcg', 0)
        })
    
    df_plot = pd.DataFrame(plot_data)
    
    # 绘制分组柱状图
    fig = px.bar(
        df_plot,
        x='experiment',
        y='value',
        color='metric',
        barmode='group',
        title='多实验指标对比',
        labels={'value': '得分', 'experiment': '实验ID'}
    )
    
    fig.update_layout(
        xaxis_title="实验ID",
        yaxis_title="得分",
        legend_title="指标",
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)


def main():
    """主函数"""
    
    # 标题
    st.markdown('<div class="main-header">📊 RAG检索质量评估系统</div>', unsafe_allow_html=True)
    
    # 侧边栏
    with st.sidebar:
        st.header("⚙️ 控制面板")
        
        # 加载实验列表
        tracker = ExperimentTracker()
        experiments = tracker.list_experiments(limit=50)
        
        if experiments:
            experiment_options = [exp['experiment_id'] for exp in experiments]
            
            selected_experiments = st.multiselect(
                "选择实验",
                options=experiment_options,
                default=[experiment_options[0]] if experiment_options else [],
                help="可选择多个实验进行对比"
            )
            
            st.divider()
            
            # 显示实验统计
            st.write(f"**实验总数:** {len(experiments)}")
            
            # 快速操作
            st.divider()
            st.header("🚀 快速操作")
            
            if st.button("🔄 刷新实验列表"):
                st.rerun()
            
            st.divider()
            
            # 帮助信息
            st.header("❓ 使用说明")
            st.markdown("""
            1. **选择实验**: 从下拉框选择一个或多个实验
            2. **查看指标**: 在概览页查看核心评估指标
            3. **对比分析**: 选择多个实验后切换到'实验对比'页签
            
            **提示**: 运行新的评估实验后，点击刷新按钮更新列表
            """)
        else:
            st.warning("暂无实验数据\n\n请先运行评估实验")
            
            st.divider()
            st.info("""
            **如何开始？**
            
            1. 准备测试数据集
            2. 运行评估命令:
            ```bash
            python -m app.evaluation.evaluation_runner
            ```
            """)
    
    # 主区域 - Tab页签
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 概览", 
        "🔍 检索质量分析", 
        "💬 答案质量分析",
        "⚖️ 实验对比"
    ])
    
    with tab1:
        show_overview_tab(selected_experiments if experiments else [])
    
    with tab2:
        show_retrieval_analysis_tab(selected_experiments if experiments else [])
    
    with tab3:
        show_generation_analysis_tab(selected_experiments if experiments else [])
    
    with tab4:
        show_experiment_comparison_tab(selected_experiments if experiments else [])
    
    # 底部说明
    st.divider()
    st.markdown(
        """
        <div style='text-align: center; color: #666; font-size: 0.9rem;'>
            RAG检索质量评估系统 | 基于多维度指标的科学评估体系
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
