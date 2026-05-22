"""
知识库问答系统 - Streamlit前端应用
"""
import streamlit as st
import os
import sys
from pathlib import Path
from typing import List
import tempfile

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from app.data_loader import DataLoader
from app.text_spliter import TextSpliter
from app.vector_db import VectorDatabase
from app.rag_chain import RAGChain
from config.settings import DOCUMENTS_DIR


# 页面配置
st.set_page_config(
    page_title="知识库问答系统",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)


# 自定义CSS样式
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: bold;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
    }
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
    }
    .assistant-message {
        background-color: #f5f5f5;
        border-left: 4px solid #4caf50;
    }
    .source-box {
        background-color: #fff3e0;
        padding: 0.5rem;
        border-radius: 0.3rem;
        margin-top: 0.5rem;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def init_rag_system():
    """
    初始化RAG系统（缓存资源）
    
    Returns:
        RAGChain实例
    """
    return RAGChain()


def save_uploaded_file(uploaded_file):
    """
    保存上传的文件到临时目录
    
    Args:
        uploaded_file: Streamlit上传的文件对象
        
    Returns:
        保存的文件路径
    """
    try:
        # 获取文件扩展名
        file_ext = os.path.splitext(uploaded_file.name)[1]
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext, dir=DOCUMENTS_DIR) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_file_path = tmp_file.name
        
        return tmp_file_path
    
    except Exception as e:
        st.error(f"保存文件失败: {str(e)}")
        return None


def process_document(file_path: str):
    """
    处理文档并添加到向量数据库
    
    Args:
        file_path: 文档文件路径
    """
    try:
        # 加载文档
        loader = DataLoader()
        documents = loader.load_document(file_path)
        
        # 分割文本
        splitter = TextSpliter()
        split_docs = splitter.split_documents(documents)
        
        # 添加到向量数据库
        vector_db = VectorDatabase()
        vector_db.initialize()
        vector_db.add_documents(split_docs)
        
        return len(split_docs)
    
    except Exception as e:
        raise Exception(f"处理文档失败: {str(e)}")


def display_chat_message(role: str, content: str, sources: List = None):
    """
    显示聊天消息
    
    Args:
        role: 角色（user/assistant）
        content: 消息内容
        sources: 来源文档列表
    """
    if role == "user":
        css_class = "user-message"
        icon = "👤"
    else:
        css_class = "assistant-message"
        icon = "🤖"
    
    st.markdown(f"""
    <div class="chat-message {css_class}">
        <strong>{icon} {"用户" if role == "user" else "助手"}</strong>
        <div style="margin-top: 0.5rem;">{content}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # 显示来源信息
    if sources and len(sources) > 0:
        with st.expander("📄 查看参考来源", expanded=False):
            for i, source in enumerate(sources, 1):
                st.markdown(f"**来源 {i}:**")
                st.markdown(f"- 文件: {source['metadata'].get('filename', '未知')}")
                st.markdown(f"- 内容预览: {source['content']}")
                st.markdown("---")


def main():
    """主函数"""
    
    # 标题
    st.markdown('<div class="main-header">知识库问答系统</div>', unsafe_allow_html=True)
    
    # 侧边栏
    with st.sidebar:
        st.header("📁 文档管理")
        
        # 文档上传
        uploaded_files = st.file_uploader(
            "上传文档",
            type=['pdf', 'docx', 'txt', 'jpg', 'jpeg', 'png', 'bmp', 'tiff', 'webp'],
            accept_multiple_files=True,
            help="支持PDF、DOCX、TXT和图片格式（JPG/PNG/BMP等）"
        )
        
        if uploaded_files:
            st.info(f"已选择 {len(uploaded_files)} 个文件")
            
            if st.button("📤 处理并上传文档", type="primary"):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                total_chunks = 0
                success_count = 0
                
                for i, uploaded_file in enumerate(uploaded_files):
                    status_text.text(f"正在处理: {uploaded_file.name}")
                    
                    # 保存文件
                    file_path = save_uploaded_file(uploaded_file)
                    
                    if file_path:
                        try:
                            # 判断是否为图片
                            file_ext = Path(uploaded_file.name).suffix.lower()
                            is_image = file_ext in {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
                            
                            if is_image:
                                status_text.text(f"正在OCR识别: {uploaded_file.name}")
                            
                            # 处理文档
                            chunks = process_document(file_path)
                            total_chunks += chunks
                            success_count += 1
                        except Exception as e:
                            st.error(f"处理文件 {uploaded_file.name} 失败: {str(e)}")
                    
                    # 更新进度条
                    progress_bar.progress((i + 1) / len(uploaded_files))
                
                status_text.text("处理完成！")
                st.success(f"✅ 成功处理 {success_count}/{len(uploaded_files)} 个文件，共 {total_chunks} 个文本块")
                
                # 如果有图片，显示OCR说明
                image_files = [f for f in uploaded_files if Path(f.name).suffix.lower() in {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}]
                if image_files:
                    st.info("💡 提示：图片已通过OCR识别提取文字内容")
        
        st.divider()
        
        # 知识库状态
        st.header("📊 知识库状态")
        try:
            vector_db = VectorDatabase()
            vector_db.initialize()
            doc_count = vector_db.get_document_count()
            st.metric("文档块数量", doc_count)
        except Exception as e:
            st.warning(f"无法获取知识库状态: {str(e)}")
        
        st.divider()
        
        # 清空知识库
        if st.button("🗑️ 清空知识库", type="secondary"):
            if st.confirm("确定要清空知识库吗？此操作不可恢复！"):
                try:
                    vector_db = VectorDatabase()
                    vector_db.initialize()
                    vector_db.delete_collection()
                    st.success("✅ 知识库已清空")
                    st.rerun()
                except Exception as e:
                    st.error(f"清空知识库失败: {str(e)}")
        
        st.divider()
        
        # 查看知识库内容
        if st.button("🔍 查看知识库内容", type="secondary"):
            try:
                vector_db = VectorDatabase()
                vector_db.initialize()
                
                # 获取所有文档
                collection = vector_db.vectorstore._collection
                results = collection.get()
                
                if results['ids']:
                    st.success(f"知识库中共有 {len(results['ids'])} 个文本块")
                    
                    # 创建可展开的列表
                    for i, (doc_id, doc_content, metadata) in enumerate(
                        zip(results['ids'], results['documents'], results['metadatas']), 1
                    ):
                        filename = metadata.get('filename', '未知')
                        doc_type = metadata.get('type', 'document')
                        
                        with st.expander(f"📄 文本块 {i}: {filename}"):
                            st.markdown(f"**类型:** {doc_type}")
                            st.markdown(f"**ID:** `{doc_id[:30]}...`")
                            
                            st.markdown("**元数据:**")
                            st.json(metadata)
                            
                            st.markdown("**文本内容:**")
                            preview_length = min(500, len(doc_content))
                            st.text_area(
                                "",
                                value=doc_content[:preview_length] + "..." if len(doc_content) > preview_length else doc_content,
                                height=150,
                                key=f"doc_{i}",
                                disabled=True
                            )
                            
                            # 显示向量信息
                            if results.get('embeddings') and i <= len(results['embeddings']):
                                embedding = results['embeddings'][i-1]
                                st.markdown(f"**向量维度:** {len(embedding)}")
                                st.markdown(f"**向量前5个值:** {[round(v, 4) for v in embedding[:5]]}")
                            
                            # 删除按钮
                            st.divider()
                            col1, col2 = st.columns([1, 4])
                            with col1:
                                if st.button(f"🗑️ 删除", key=f"delete_{doc_id}"):
                                    try:
                                        # 删除该文档块
                                        collection.delete(ids=[doc_id])
                                        st.success("✅ 已删除")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"删除失败: {str(e)}")
                            with col2:
                                st.caption(f"点击删除此文本块")
                else:
                    st.warning("知识库为空，请先上传文档")
            
            except Exception as e:
                st.error(f"查看知识库失败: {str(e)}")
        
        st.divider()
        
        # 搜索文本块
        st.header("🔎 搜索文本块")
        
        search_query = st.text_input("输入关键词搜索", placeholder="例如：合同、错误、代码...")
        
        if search_query and st.button("🔍 搜索", key="search_btn"):
            try:
                vector_db = VectorDatabase()
                vector_db.initialize()
                
                # 使用相似性搜索
                results = vector_db.similarity_search_with_score(search_query, k=10)
                
                if results:
                    st.success(f"找到 {len(results)} 个相关文本块")
                    
                    for i, (doc, score) in enumerate(results, 1):
                        filename = doc.metadata.get('filename', '未知')
                        doc_type = doc.metadata.get('type', 'document')
                        
                        with st.expander(f"📝 结果 {i} (相似度: {score:.4f}) - {filename}"):
                            st.markdown(f"**类型:** {doc_type}")
                            st.markdown(f"**文件:** {filename}")
                            
                            st.markdown("**内容:**")
                            st.text_area(
                                "",
                                value=doc.page_content,
                                height=200,
                                key=f"search_{i}",
                                disabled=True
                            )
                            
                            st.markdown("**完整元数据:**")
                            st.json(doc.metadata)
                else:
                    st.warning("未找到相关内容")
            
            except Exception as e:
                st.error(f"搜索失败: {str(e)}")
        
        st.divider()
        
        # 批量删除功能
        st.header("🗂️ 批量管理")
        
        try:
            vector_db = VectorDatabase()
            vector_db.initialize()
            
            collection = vector_db.vectorstore._collection
            results = collection.get()
            
            if results['ids']:
                # 统计每个文件的文本块数量
                file_stats = {}
                for metadata in results['metadatas']:
                    filename = metadata.get('filename', '未知')
                    if filename not in file_stats:
                        file_stats[filename] = 0
                    file_stats[filename] += 1
                
                # 显示文件列表和删除选项
                st.markdown(f"**当前知识库中有 {len(file_stats)} 个文件，共 {len(results['ids'])} 个文本块**")
                
                # 创建文件选择器
                selected_files = st.multiselect(
                    "选择要删除的文件",
                    options=list(file_stats.keys()),
                    format_func=lambda x: f"{x} ({file_stats[x]} 个文本块)"
                )
                
                if selected_files:
                    st.warning(f"⚠️ 将删除 {len(selected_files)} 个文件的所有文本块")
                    
                    # 显示将要删除的详情
                    for filename in selected_files:
                        st.caption(f"• {filename}: {file_stats[filename]} 个文本块")
                    
                    if st.button("🗑️ 确认删除选中文件", type="primary", key="batch_delete"):
                        try:
                            deleted_count = 0
                            # 获取所有要删除的文档ID
                            ids_to_delete = []
                            for doc_id, metadata in zip(results['ids'], results['metadatas']):
                                if metadata.get('filename') in selected_files:
                                    ids_to_delete.append(doc_id)
                            
                            # 批量删除
                            if ids_to_delete:
                                collection.delete(ids=ids_to_delete)
                                deleted_count = len(ids_to_delete)
                                st.success(f"✅ 成功删除 {deleted_count} 个文本块")
                                st.rerun()
                        except Exception as e:
                            st.error(f"批量删除失败: {str(e)}")
            else:
                st.info("知识库为空")
        
        except Exception as e:
            st.error(f"加载文件列表失败: {str(e)}")
        
        st.divider()
        
        # 向量可视化
        st.header("📊 向量可视化")
        
        if st.button("🎨 生成向量分布图", type="secondary"):
            try:
                import numpy as np
                from sklearn.manifold import TSNE
                import plotly.express as px
                
                vector_db = VectorDatabase()
                vector_db.initialize()
                
                collection = vector_db.vectorstore._collection
                results = collection.get()
                
                if not results['ids'] or not results.get('embeddings'):
                    st.warning("知识库为空或没有向量数据")
                else:
                    with st.spinner("正在降维处理..."):
                        # 获取向量和元数据
                        embeddings = np.array(results['embeddings'])
                        filenames = [m.get('filename', '未知') for m in results['metadatas']]
                        doc_types = [m.get('type', 'document') for m in results['metadatas']]
                        
                        # 使用t-SNE降维到2D
                        tsne = TSNE(n_components=2, random_state=42, perplexity=min(30, len(embeddings)-1))
                        embeddings_2d = tsne.fit_transform(embeddings)
                        
                        # 创建DataFrame
                        import pandas as pd
                        df = pd.DataFrame({
                            'x': embeddings_2d[:, 0],
                            'y': embeddings_2d[:, 1],
                            'filename': filenames,
                            'type': doc_types,
                            'id': results['ids']
                        })
                        
                        # 绘制交互式散点图
                        fig = px.scatter(
                            df,
                            x='x',
                            y='y',
                            color='type',
                            hover_data=['filename', 'id'],
                            title='知识库向量分布图（t-SNE降维）',
                            labels={'x': '维度 1', 'y': '维度 2'},
                            color_discrete_map={'document': '#1f77b4', 'image': '#ff7f0e'}
                        )
                        
                        fig.update_traces(marker=dict(size=8, opacity=0.7))
                        fig.update_layout(height=600, width=800)
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        st.info("💡 提示：鼠标悬停可查看详细信息，相同颜色的点表示同类型文档")
            
            except ImportError:
                st.error("缺少可视化库，请运行: pip install scikit-learn plotly pandas")
            except Exception as e:
                st.error(f"可视化失败: {str(e)}")
                st.exception(e)
        
        st.divider()
        
        # 帮助信息
        st.header("❓ 使用说明")
        st.markdown("""
        1. **上传文档**: 在侧边栏上传PDF、DOCX、TXT或图片文件
        2. **处理文档**: 点击'处理并上传文档'按钮
           - 图片文件会自动进行OCR识别
        3. **开始提问**: 在主界面输入您的问题
        4. **查看来源**: 点击回答下方的'查看参考来源'
        
        **支持的图片格式**：JPG、PNG、BMP、TIFF、WEBP
        """)
    
    # 主聊天区域
    st.subheader("💬 开始对话")
    
    # 初始化会话状态
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "rag_chain" not in st.session_state:
        with st.spinner("正在初始化RAG系统..."):
            st.session_state.rag_chain = init_rag_system()
    
    # 显示历史消息
    for message in st.session_state.messages:
        display_chat_message(
            message["role"],
            message["content"],
            message.get("sources")
        )
    
    # 聊天输入框
    if prompt := st.chat_input("请输入您的问题..."):
        # 显示用户消息
        st.session_state.messages.append({"role": "user", "content": prompt})
        display_chat_message("user", prompt)
        
        # 生成AI回答
        with st.spinner("正在思考中..."):
            try:
                rag_chain = st.session_state.rag_chain
                result = rag_chain.query(prompt, k=5)
                
                answer = result['answer']
                sources = result['sources']
                
                # 显示AI回答
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "sources": sources
                })
                display_chat_message("assistant", answer, sources)
                
            except Exception as e:
                error_msg = f"抱歉，处理您的问题时出现了错误: {str(e)}"
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg
                })
                display_chat_message("assistant", error_msg)
    
    # 底部说明
    st.divider()
    st.markdown(
        """
        <div style='text-align: center; color: #666; font-size: 0.9rem;'>
            知识库问答系统 | 基于RAG技术构建
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
