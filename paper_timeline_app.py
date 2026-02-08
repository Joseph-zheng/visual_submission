import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from datetime import datetime, timedelta
import matplotlib.dates as mdates
import io
import json
import os

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

st.set_page_config(page_title="论文审稿流程可视化", layout="wide")

st.title("📊 学术论文审稿流程甘特图生成器")
st.markdown("---")

# JSON配置文件路径
CONFIG_FILE = "paper_timeline_config.json"

# 加载配置函数
def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return None
    return None

# 保存配置函数
def save_config(data):
    # 转换datetime对象为字符串
    config_data = {
        'num_papers': len(data),
        'papers': []
    }
    for paper in data:
        paper_config = {
            'name': paper['name'],
            'submit_date': paper['submit_date'].strftime('%Y-%m-%d'),
            'status': paper['status'],
            'stages': []
        }
        for stage in paper['stages']:
            stage_config = {
                'type': stage['type'],
                'start_date': stage['start_date'].strftime('%Y-%m-%d'),
                'end_date': stage['end_date'].strftime('%Y-%m-%d'),
                'show_label': stage['show_label']
            }
            paper_config['stages'].append(stage_config)
        config_data['papers'].append(paper_config)
    
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, ensure_ascii=False, indent=2)

# 尝试加载已保存的配置
saved_config = load_config()

# 侧边栏：论文数量选择
st.sidebar.header("⚙️ 配置")

# 如果有保存的配置，使用保存的论文数量
default_num_papers = saved_config['num_papers'] if saved_config else 2
num_papers = st.sidebar.number_input("论文数量", min_value=1, max_value=5, value=default_num_papers, step=1)

# 颜色定义
colors = {
    'submit': '#3498DB',
    'editor': '#E74C3C',
    'review1': '#2ECC71',
    'revise': '#F39C12',
    'review2': '#9B59B6',
    'review3': '#1ABC9C',
    'review4': '#E67E22'
}

# 存储所有论文数据
papers_data = []

# 为每篇论文创建输入区域
for i in range(num_papers):
    st.subheader(f"📄 论文 {i+1}")
    
    # 从保存的配置中获取默认值
    saved_paper = None
    if saved_config and i < len(saved_config['papers']):
        saved_paper = saved_config['papers'][i]
    
    col1, col2 = st.columns(2)
    
    with col1:
        default_name = saved_paper['name'] if saved_paper else f"论文{i+1}"
        paper_name = st.text_input(f"论文名称", value=default_name, key=f"name_{i}")
        
        default_submit = datetime.strptime(saved_paper['submit_date'], '%Y-%m-%d').date() if saved_paper else (datetime(2025, 6, 22) if i == 0 else datetime(2025, 11, 13)).date()
        submit_date = st.date_input(f"提交日期", value=default_submit, key=f"submit_{i}")
    
    with col2:
        default_status = saved_paper['status'] if saved_paper else ("审稿中" if i == 0 else "返修中")
        status_options = ["已提交", "With Editor", "审稿中", "返修中", "已接收", "已拒稿"]
        default_status_index = status_options.index(default_status) if default_status in status_options else 2
        status = st.selectbox(f"当前状态", 
                             status_options, 
                             index=default_status_index, 
                             key=f"status_{i}")
    
    # 阶段输入
    st.markdown("**审稿阶段（按时间顺序）**")
    
    default_num_stages = len(saved_paper['stages']) if saved_paper else (5 if i == 0 else 4)
    num_stages = st.number_input(f"阶段数量", min_value=1, max_value=10, value=default_num_stages, key=f"stages_{i}")
    
    stages = []
    
    # 计算当前累计日期
    current_calc_date = datetime.combine(submit_date, datetime.min.time())
    
    # 预设的默认日期（论文1和论文2）
    default_dates_paper1 = [
        (datetime(2025, 6, 22), datetime(2025, 7, 20)),   # 阶段1: 28天
        (datetime(2025, 7, 20), datetime(2025, 7, 24)),   # 阶段2: 4天
        (datetime(2025, 7, 24), datetime(2025, 9, 30)),   # 阶段3: 68天
        (datetime(2025, 9, 30), datetime(2025, 10, 10)),  # 阶段4: 10天
        (datetime(2025, 10, 10), datetime(2025, 11, 16)), # 阶段5: 37天
    ]
    
    default_dates_paper2 = [
        (datetime(2025, 11, 13), datetime(2025, 11, 14)), # 阶段1: 1天
        (datetime(2025, 11, 14), datetime(2025, 12, 18)), # 阶段2: 34天
        (datetime(2025, 12, 18), datetime(2026, 1, 6)),   # 阶段3: 19天
        (datetime(2026, 1, 6), datetime(2026, 1, 31)),    # 阶段4: 25天
    ]
    
    # 一行三个阶段的布局
    for row_start in range(0, num_stages, 3):
        cols = st.columns(3)
        for col_idx in range(3):
            j = row_start + col_idx
            if j >= num_stages:
                break
            
            with cols[col_idx]:
                with st.expander(f"阶段 {j+1}", expanded=False):
                    # 从保存的配置中获取默认值
                    saved_stage = None
                    if saved_paper and j < len(saved_paper['stages']):
                        saved_stage = saved_paper['stages'][j]
                    
                    default_stage_type = saved_stage['type'] if saved_stage else (["提交→With Editor", "With Editor", "第1轮审稿", "返修期", "第2轮审稿"][j] if j < 5 else "提交→With Editor")
                    stage_options = ["提交→With Editor", "With Editor", "第1轮审稿", "返修期", "第2轮审稿", "第3轮审稿", "第4轮审稿"]
                    default_stage_index = stage_options.index(default_stage_type) if default_stage_type in stage_options else 0
                    
                    stage_type = st.selectbox(
                        "阶段类型",
                        stage_options,
                        index=default_stage_index,
                        key=f"type_{i}_{j}"
                    )
                    
                    # 设置默认开始日期
                    if saved_stage:
                        default_start = datetime.strptime(saved_stage['start_date'], '%Y-%m-%d').date()
                    elif i == 0 and j < len(default_dates_paper1):
                        default_start = default_dates_paper1[j][0].date()
                    elif i == 1 and j < len(default_dates_paper2):
                        default_start = default_dates_paper2[j][0].date()
                    else:
                        default_start = current_calc_date.date()
                    
                    start_date = st.date_input("开始日期", value=default_start, key=f"start_{i}_{j}")
                    
                    # 判断是否是最后一个阶段且状态不是"已接收"
                    is_ongoing = (j == num_stages - 1) and (status != "已接收")
                    
                    if is_ongoing:
                        # 如果是进行中的阶段，结束日期默认为今天
                        default_end = datetime.now().date()
                        end_date = st.date_input("结束日期（进行中）", value=default_end, key=f"end_{i}_{j}")
                    else:
                        # 设置默认结束日期
                        if saved_stage:
                            default_end = datetime.strptime(saved_stage['end_date'], '%Y-%m-%d').date()
                        elif i == 0 and j < len(default_dates_paper1):
                            default_end = default_dates_paper1[j][1].date()
                        elif i == 1 and j < len(default_dates_paper2):
                            default_end = default_dates_paper2[j][1].date()
                        else:
                            # 转换为datetime再加天数
                            start_dt_temp = datetime.combine(start_date, datetime.min.time())
                            default_end = (start_dt_temp + timedelta(days=10)).date()
                        
                        end_date = st.date_input("结束日期", value=default_end, key=f"end_{i}_{j}")
                    
                    default_show_label = saved_stage['show_label'] if saved_stage else True
                    show_label = st.checkbox("显示标签", value=default_show_label, key=f"label_{i}_{j}")
                    
                    # 计算持续天数
                    start_dt = datetime.combine(start_date, datetime.min.time())
                    end_dt = datetime.combine(end_date, datetime.min.time())
                    duration = (end_dt - start_dt).days
                    
                    stages.append({
                        'type': stage_type,
                        'start_date': start_dt,
                        'end_date': end_dt,
                        'duration': duration,
                        'show_label': show_label,
                        'is_ongoing': is_ongoing
                    })
                    
                    # 更新下一个阶段的默认开始日期
                    current_calc_date = end_dt
    
    papers_data.append({
        'name': paper_name,
        'submit_date': datetime.combine(submit_date, datetime.min.time()),
        'status': status,
        'stages': stages
    })
    
    st.markdown("---")

# 生成按钮
if st.button("🎨 生成甘特图", type="primary", use_container_width=True):
    
    # 保存配置到JSON文件
    save_config(papers_data)
    st.success(f"✅ 配置已保存到 {CONFIG_FILE}")
    
    # 计算时间范围
    all_dates = []
    for paper in papers_data:
        all_dates.append(paper['submit_date'])
        for stage in paper['stages']:
            all_dates.append(stage['end_date'])
    
    start_date = min(all_dates) - timedelta(days=30)
    end_date = max(all_dates) + timedelta(days=30)
    
    # 创建图表
    fig, ax = plt.subplots(figsize=(16, 2 + num_papers * 2))
    ax.set_xlim(start_date, end_date)
    ax.set_ylim(0, num_papers * 3 + 1)
    
    # 绘制函数 - 去掉黑色外框
    def draw_task(ax, start, duration, color, label, y_pos, show_label):
        ax.broken_barh([(start, duration)], (y_pos, 0.7), 
                       facecolors=color, edgecolor='none', linewidth=0, alpha=0.9)
        if show_label:
            center = start + duration/2
            ax.text(center, y_pos + 0.35, label, ha='center', va='center', 
                   fontsize=8, fontweight='bold', color='#1C2833',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white', 
                            alpha=0.9, edgecolor='gray', linewidth=1))
    
    # 绘制每篇论文
    y_positions = []
    y_labels = []
    used_stage_types = set()  # 记录所有使用的阶段类型
    
    for idx, paper in enumerate(papers_data):
        y_pos = (num_papers - idx) * 3 - 0.5
        y_positions.append(y_pos + 0.35)
        
        # 绘制各阶段
        for stage in paper['stages']:
            stage_type = stage['type']
            duration_days = stage['duration']
            
            # 记录使用的阶段类型
            used_stage_types.add(stage_type)
            
            # 确定颜色
            if '提交' in stage_type or 'submit' in stage_type.lower():
                color = colors['submit']
            elif 'editor' in stage_type.lower() or '编辑' in stage_type:
                color = colors['editor']
            elif '第1轮' in stage_type or '一审' in stage_type:
                color = colors['review1']
            elif '返修' in stage_type:
                color = colors['revise']
            elif '第2轮' in stage_type or '二审' in stage_type:
                color = colors['review2']
            elif '第3轮' in stage_type or '三审' in stage_type:
                color = colors['review3']
            elif '第4轮' in stage_type or '四审' in stage_type:
                color = colors['review4']
            else:
                color = '#95A5A6'
            
            # 只显示天数
            label = f"{duration_days}天"
            draw_task(ax, stage['start_date'], timedelta(days=duration_days), color, label, y_pos, stage['show_label'])
        
        # 计算结束日期
        if paper['status'] == '已接收':
            end_date_display = paper['stages'][-1]['end_date']
        else:
            end_date_display = datetime.now()
        
        # Y轴标签 - 三行格式：论文名称 / 日期范围 / 状态
        y_labels.append(f'{paper["name"]}\n{paper["submit_date"].strftime("%Y.%m.%d")} - {end_date_display.strftime("%Y.%m.%d")}\n({paper["status"]})')
        
        # 总周期标注 - 移到下方
        total_days = sum(s['duration'] for s in paper['stages'])
        mid_date = paper['submit_date'] + timedelta(days=total_days/2)
        
        ax.annotate('', xy=(paper['stages'][-1]['end_date'], y_pos - 0.3), 
                    xytext=(paper['submit_date'], y_pos - 0.3),
                    arrowprops=dict(arrowstyle='<->', color='#34495E', lw=2))
        ax.text(mid_date, y_pos - 0.6, f'总周期: {total_days}天', 
               ha='center', fontsize=9, fontweight='bold', color='white',
               bbox=dict(boxstyle='round,pad=0.4', facecolor='#34495E', edgecolor='#2C3E50', linewidth=1.5))
        
        # 背景色
        bg_colors = ['#FADBD8', '#D6EAF8', '#D5F4E6', '#FCF3CF', '#EBDEF0']
        ax.axhspan(y_pos - 0.5, y_pos + 2, facecolor=bg_colors[idx % len(bg_colors)], alpha=0.2, zorder=0)
    
    # Y轴设置
    ax.set_yticks(y_positions)
    ax.set_yticklabels(y_labels, fontsize=10, fontweight='bold')
    ax.tick_params(axis='y', length=0, pad=15)
    
    # X轴设置
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y年%m月'))
    ax.xaxis.set_minor_locator(mdates.WeekdayLocator(interval=2))
    plt.xticks(rotation=0, fontsize=10)
    
    # 今日参考线
    today = datetime.now()
    if start_date <= today <= end_date:
        ax.axvline(x=today, color='#E74C3C', linestyle='--', linewidth=3, alpha=0.7)
        ax.text(today, num_papers * 3 + 0.5, '今日', rotation=0, ha='center', va='bottom', 
               fontsize=10, fontweight='bold', color='#C0392B',
               bbox=dict(boxstyle='round,pad=0.4', facecolor='#FADBD8', edgecolor='#E74C3C', linewidth=1.5))
    
    # 网格
    ax.grid(True, axis='x', which='major', alpha=0.5, linestyle='-', linewidth=1, color='gray')
    ax.grid(True, axis='x', which='minor', alpha=0.2, linestyle=':', linewidth=0.5)
    ax.set_axisbelow(True)
    
    # 图例 - 动态显示，只显示实际使用的阶段类型
    stage_type_mapping = {
        '提交→With Editor': ('submit', '提交 → With Editor'),
        'With Editor': ('editor', 'With Editor'),
        '第1轮审稿': ('review1', '第1轮审稿'),
        '返修期': ('revise', '返修期'),
        '第2轮审稿': ('review2', '第2轮审稿'),
        '第3轮审稿': ('review3', '第3轮审稿'),
        '第4轮审稿': ('review4', '第4轮审稿')
    }
    
    legend_elements = []
    for stage_type in ['提交→With Editor', 'With Editor', '第1轮审稿', '返修期', '第2轮审稿', '第3轮审稿', '第4轮审稿']:
        if stage_type in used_stage_types:
            color_key, label = stage_type_mapping[stage_type]
            legend_elements.append(
                mpatches.Patch(facecolor=colors[color_key], edgecolor='none', label=label)
            )
    
    # 动态调整列数
    ncol = min(len(legend_elements), 7)
    legend = ax.legend(handles=legend_elements, loc='upper center', 
                       bbox_to_anchor=(0.5, -0.05), ncol=ncol, fontsize=10, 
                       frameon=False, columnspacing=2.5, handlelength=3, handleheight=1.5)
    
    # 标题
    ax.set_title('学术论文审稿流程甘特图', 
                 fontsize=18, fontweight='bold', pad=20, color='#2C3E50')
    
    # 边框
    for spine in ['top', 'right', 'left']:
        ax.spines[spine].set_visible(False)
    ax.spines['bottom'].set_color('#34495E')
    ax.spines['bottom'].set_linewidth(3)
    
    plt.tight_layout()
    
    # 显示图表
    st.pyplot(fig)
    
    # 下载按钮
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=200, bbox_inches='tight', facecolor='white')
    buf.seek(0)
    
    st.download_button(
        label="📥 下载甘特图 (PNG)",
        data=buf,
        file_name=f"paper_timeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
        mime="image/png",
        use_container_width=True
    )
    
    plt.close()

# 使用说明
with st.sidebar.expander("📖 使用说明"):
    st.markdown("""
    ### 如何使用
    1. 设置论文数量
    2. 为每篇论文填写：
       - 论文名称
       - 提交日期
       - 当前状态
    3. 添加审稿阶段：
       - 选择阶段类型
       - 输入开始和结束日期
       - 程序自动计算持续天数
       - 选择是否显示标签
    4. 点击"生成甘特图"
    5. 下载生成的图表
    
    ### 阶段类型说明
    - **提交→With Editor**: 初次提交到编辑处理
    - **With Editor**: 编辑审核阶段
    - **第1轮审稿**: 首次外审
    - **返修期**: 作者修改时间
    - **第2轮审稿**: 返修后再审
    - **第3轮审稿**: 第三轮审稿
    - **第4轮审稿**: 第四轮审稿
    
    ### 提示
    - 如果论文状态不是"已接收"，最后一个阶段的结束日期默认为今天
    - 图表会自动计算总周期并显示在图形下方
    - 配置会自动保存到JSON文件，下次打开自动加载
    """)

st.sidebar.markdown("---")
st.sidebar.info("💡 提示：修改参数后点击'生成甘特图'查看效果")
