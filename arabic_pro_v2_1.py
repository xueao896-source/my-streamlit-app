#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专业级阿拉伯语学习平台 - 修复版 v2.1
解决所有语法错误
"""

import streamlit as st
import sqlite3
from datetime import datetime, timedelta
import pandas as pd
from gtts import gTTS
import io

st.set_page_config(page_title="阿拉伯语学习平台", page_icon="🌍", layout="wide")

DB_PATH = "arabic_learning.db"

# ============ 数据库初始化 ============

def init_database():
    """初始化数据库"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT DEFAULT 'student',
        created_at TEXT
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS lessons (
        id INTEGER PRIMARY KEY,
        title TEXT UNIQUE,
        description TEXT,
        category TEXT,
        level TEXT,
        order_num INTEGER
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS vocabulary (
        id INTEGER PRIMARY KEY,
        lesson_id INTEGER,
        arabic TEXT,
        english TEXT,
        pronunciation TEXT,
        example TEXT,
        FOREIGN KEY(lesson_id) REFERENCES lessons(id)
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS user_progress (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        vocab_id INTEGER,
        review_count INTEGER DEFAULT 0,
        next_review_date TEXT,
        difficulty_level INTEGER DEFAULT 1,
        UNIQUE(user_id, vocab_id),
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(vocab_id) REFERENCES vocabulary(id)
    )''')
    
    conn.commit()
    conn.close()

# ============ 初始语料库 ============

INITIAL_LESSONS = [
    {
        "title": "1️⃣ 问候与礼貌",
        "description": "基础问候和礼貌用语",
        "category": "基础",
        "level": "初级",
        "vocabulary": [
            {"arabic": "السلام عليكم", "english": "Peace be upon you", "pronunciation": "As-salaam alaikum", "example": "正式问候"},
            {"arabic": "وعليكم السلام", "english": "And upon you be peace", "pronunciation": "Wa alaikum as-salam", "example": "问候回应"},
            {"arabic": "صباح الخير", "english": "Good morning", "pronunciation": "Sabah al-khair", "example": "早上问候"},
            {"arabic": "مساء الخير", "english": "Good evening", "pronunciation": "Masaa al-khair", "example": "晚上问候"},
            {"arabic": "كيف حالك", "english": "How are you?", "pronunciation": "Kayf halak", "example": "询问状态"},
            {"arabic": "تمام التمام", "english": "I'm fine", "pronunciation": "Tamam at-tamam", "example": "回答问候"},
            {"arabic": "شكرا لك", "english": "Thank you", "pronunciation": "Shukran lak", "example": "表示感谢"},
            {"arabic": "عفوا", "english": "You're welcome", "pronunciation": "Afwan", "example": "回应感谢"},
            {"arabic": "من فضلك", "english": "Please", "pronunciation": "Min fadlak", "example": "礼貌请求"},
            {"arabic": "أسف", "english": "Sorry", "pronunciation": "Asif", "example": "道歉"},
        ]
    },
    {
        "title": "2️⃣ 食物与饮品",
        "description": "食物、饮料相关词汇",
        "category": "日常生活",
        "level": "初级",
        "vocabulary": [
            {"arabic": "الماء", "english": "Water", "pronunciation": "Al-maa", "example": "饮料"},
            {"arabic": "خبز", "english": "Bread", "pronunciation": "Khubz", "example": "主食"},
            {"arabic": "تفاح", "english": "Apple", "pronunciation": "Tuffah", "example": "水果"},
            {"arabic": "برتقال", "english": "Orange", "pronunciation": "Burtuqal", "example": "柑橘类"},
            {"arabic": "دجاج", "english": "Chicken", "pronunciation": "Dajaj", "example": "肉类"},
            {"arabic": "سمك", "english": "Fish", "pronunciation": "Samak", "example": "海产品"},
            {"arabic": "حليب", "english": "Milk", "pronunciation": "Haleeb", "example": "饮品"},
            {"arabic": "قهوة", "english": "Coffee", "pronunciation": "Qahwa", "example": "饮品"},
            {"arabic": "شاي", "english": "Tea", "pronunciation": "Shay", "example": "饮品"},
            {"arabic": "طعام", "english": "Food", "pronunciation": "Ta'am", "example": "通用术语"},
        ]
    },
    {
        "title": "3️⃣ 数字 1-10",
        "description": "基础数字",
        "category": "基础",
        "level": "初级",
        "vocabulary": [
            {"arabic": "واحد", "english": "One", "pronunciation": "Wahid", "example": "数字1"},
            {"arabic": "اثنين", "english": "Two", "pronunciation": "Ithnain", "example": "数字2"},
            {"arabic": "ثلاثة", "english": "Three", "pronunciation": "Thalatha", "example": "数字3"},
            {"arabic": "أربعة", "english": "Four", "pronunciation": "Arba'a", "example": "数字4"},
            {"arabic": "خمسة", "english": "Five", "pronunciation": "Khamsah", "example": "数字5"},
            {"arabic": "ستة", "english": "Six", "pronunciation": "Sitta", "example": "数字6"},
            {"arabic": "سبعة", "english": "Seven", "pronunciation": "Saba'a", "example": "数字7"},
            {"arabic": "ثمانية", "english": "Eight", "pronunciation": "Tamaniya", "example": "数字8"},
            {"arabic": "تسعة", "english": "Nine", "pronunciation": "Tisa'a", "example": "数字9"},
            {"arabic": "عشرة", "english": "Ten", "pronunciation": "Ashara", "example": "数字10"},
        ]
    },
]

def load_initial_data():
    """加载初始数据"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("SELECT COUNT(*) FROM lessons")
    if c.fetchone()[0] > 0:
        conn.close()
        return
    
    for i, lesson in enumerate(INITIAL_LESSONS, 1):
        c.execute('''INSERT INTO lessons (title, description, category, level, order_num)
                     VALUES (?, ?, ?, ?, ?)''',
                  (lesson['title'], lesson['description'], lesson['category'], 
                   lesson['level'], i))
        lesson_id = c.lastrowid
        
        for vocab in lesson['vocabulary']:
            c.execute('''INSERT INTO vocabulary (lesson_id, arabic, english, pronunciation, example)
                         VALUES (?, ?, ?, ?, ?)''',
                      (lesson_id, vocab['arabic'], vocab['english'], 
                       vocab['pronunciation'], vocab['example']))
    
    conn.commit()
    conn.close()

# ============ 数据库操作函数 ============

def get_lessons_from_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM lessons ORDER BY order_num")
    lessons = c.fetchall()
    conn.close()
    return lessons

def get_vocabulary_from_db(lesson_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM vocabulary WHERE lesson_id = ?", (lesson_id,))
    vocab = c.fetchall()
    conn.close()
    return vocab

def add_lesson_to_db(title, description, category, level):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("SELECT MAX(order_num) FROM lessons")
        max_order = c.fetchone()[0] or 0
        
        c.execute('''INSERT INTO lessons (title, description, category, level, order_num)
                     VALUES (?, ?, ?, ?, ?)''',
                  (title, description, category, level, max_order + 1))
        conn.commit()
        lesson_id = c.lastrowid
        return True, lesson_id, "课程添加成功"
    except sqlite3.IntegrityError:
        return False, None, "课程标题已存在"
    except Exception as e:
        return False, None, f"错误：{str(e)}"
    finally:
        conn.close()

def add_vocabulary_to_db(lesson_id, arabic, english, pronunciation, example):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute('''INSERT INTO vocabulary (lesson_id, arabic, english, pronunciation, example)
                     VALUES (?, ?, ?, ?, ?)''',
                  (lesson_id, arabic, english, pronunciation, example))
        conn.commit()
        return True, "词汇添加成功"
    except Exception as e:
        return False, f"错误：{str(e)}"
    finally:
        conn.close()

def delete_lesson_from_db(lesson_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("DELETE FROM vocabulary WHERE lesson_id = ?", (lesson_id,))
        c.execute("DELETE FROM lessons WHERE id = ?", (lesson_id,))
        conn.commit()
        return True, "课程已删除"
    except Exception as e:
        return False, f"错误：{str(e)}"
    finally:
        conn.close()

def delete_vocabulary_from_db(vocab_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("DELETE FROM vocabulary WHERE id = ?", (vocab_id,))
        conn.commit()
        return True, "词汇已删除"
    except Exception as e:
        return False, f"错误：{str(e)}"
    finally:
        conn.close()

def export_to_csv():
    """导出数据为CSV"""
    conn = sqlite3.connect(DB_PATH)
    
    lessons_df = pd.read_sql_query("SELECT id, title, description, category, level FROM lessons ORDER BY id", conn)
    vocab_df = pd.read_sql_query("SELECT lesson_id, arabic, english, pronunciation, example FROM vocabulary", conn)
    
    conn.close()
    
    return lessons_df, vocab_df

def import_vocabulary_from_csv(uploaded_file, lesson_name):
    """导入CSV词汇"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        # 获取课程ID
        c.execute("SELECT id FROM lessons WHERE title = ?", (lesson_name,))
        result = c.fetchone()
        
        if not result:
            return False, "❌ 错误：找不到指定的课程"
        
        lesson_id = result[0]
        
        # 读取CSV文件
        df = pd.read_csv(uploaded_file, encoding='utf-8-sig')
        
        # 检查必要的列
        required_columns = ['arabic', 'english', 'pronunciation', 'example']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            return False, f"❌ 错误：CSV文件缺少列：{', '.join(missing_columns)}"
        
        # 插入数据
        count = 0
        errors = []
        
        for idx, row in df.iterrows():
            try:
                c.execute('''INSERT INTO vocabulary (lesson_id, arabic, english, pronunciation, example)
                           VALUES (?, ?, ?, ?, ?)''',
                         (lesson_id, str(row['arabic']), str(row['english']), 
                          str(row['pronunciation']), str(row['example'])))
                count += 1
            except Exception as e:
                errors.append(f"第{idx+2}行出错：{str(e)}")
        
        conn.commit()
        
        if errors:
            error_msg = "\n".join(errors[:5])
            return True, f"✅ 导入成功：{count}个词汇\n⚠️ 部分行出错：\n{error_msg}"
        
        return True, f"✅ 导入成功：{count}个词汇已添加到【{lesson_name}】"
    
    except UnicodeDecodeError:
        return False, "❌ 错误：文件编码问题。请使用UTF-8编码保存CSV文件"
    except pd.errors.ParserError:
        return False, "❌ 错误：CSV文件格式不正确。请检查分隔符是否为逗号"
    except Exception as e:
        return False, f"❌ 导入失败：{str(e)}"
    finally:
        conn.close()

# ============ Session 状态 ============

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.role = None

# ============ 主程序 ============

def main():
    st.title("🌍 专业级阿拉伯语学习平台 v2.1")
    st.markdown("✅ 修复版本 - 所有错误已解决")
    st.markdown("---")
    
    init_database()
    load_initial_data()
    
    # 用户管理
    st.sidebar.title("👤 用户管理")
    
    if not st.session_state.logged_in:
        tab1, tab2 = st.sidebar.tabs(["登录", "注册"])
        
        with tab1:
            st.subheader("登录")
            username = st.text_input("用户名", key="login_user")
            password = st.text_input("密码", type="password", key="login_pass")
            role = st.selectbox("用户类型", ["学生", "管理员"], key="login_role")
            
            if st.button("登录"):
                if username and password:
                    conn = sqlite3.connect(DB_PATH)
                    c = conn.cursor()
                    
                    db_role = "admin" if role == "管理员" else "student"
                    c.execute("SELECT * FROM users WHERE username = ? AND password = ? AND role = ?",
                             (username, password, db_role))
                    user = c.fetchone()
                    
                    if user:
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.session_state.role = db_role
                        st.success("✓ 登录成功！")
                        st.rerun()
                    else:
                        try:
                            c.execute('''INSERT INTO users (username, password, role, created_at)
                                       VALUES (?, ?, ?, ?)''',
                                     (username, password, db_role, datetime.now().isoformat()))
                            conn.commit()
                            
                            st.session_state.logged_in = True
                            st.session_state.username = username
                            st.session_state.role = db_role
                            st.success("✓ 自动创建用户并登录成功！")
                            st.rerun()
                        except:
                            st.error("登录失败")
                    
                    conn.close()
    
    else:
        st.sidebar.write(f"**👋 {st.session_state.username}** ({st.session_state.role})")
        if st.sidebar.button("退出登录"):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.session_state.role = None
            st.rerun()
        
        st.sidebar.markdown("---")
        
        # 菜单
        if st.session_state.role == "admin":
            menu = st.sidebar.radio("📚 管理菜单",
                ["📖 学习", "⚙️ 管理课程", "📝 管理词汇", "📥 导入/导出", "📊 统计"])
        else:
            menu = st.sidebar.radio("📚 学习菜单",
                ["📖 课程学习", "📊 学习统计"])
        
        # ============ 学生功能 ============
        if menu == "📖 课程学习":
            st.header("📖 课程学习（包含语音）")
            
            lessons = get_lessons_from_db()
            lesson_options = {f"{l[1]}": l[0] for l in lessons}
            
            selected_lesson_name = st.selectbox("选择课程", list(lesson_options.keys()))
            lesson_id = lesson_options[selected_lesson_name]
            
            vocab_list = get_vocabulary_from_db(lesson_id)
            st.write(f"本课程共 **{len(vocab_list)}** 个单词")
            
            cols = st.columns(2)
            for i, vocab in enumerate(vocab_list):
                with cols[i % 2]:
                    with st.container(border=True):
                        st.markdown(f"### {vocab[2]}")
                        st.write(f"📍 {vocab[4]}")
                        st.write(f"🇬🇧 {vocab[3]}")
                        st.write(f"📝 {vocab[5]}")
                        
                        if st.button(f"🔊 听发音", key=f"voice_{vocab[0]}"):
                            try:
                                tts = gTTS(vocab[2], lang='ar')
                                audio_bytes = io.BytesIO()
                                tts.write_to_fp(audio_bytes)
                                audio_bytes.seek(0)
                                st.audio(audio_bytes, format="audio/mp3")
                            except:
                                st.warning("⚠️ 需要网络连接")
        
        elif menu == "📊 学习统计":
            st.header("📊 学习统计")
            
            lessons = get_lessons_from_db()
            total_vocab = sum(len(get_vocabulary_from_db(l[0])) for l in lessons)
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("总课程数", len(lessons))
            with col2:
                st.metric("总词汇数", total_vocab)
            
            st.markdown("---")
            st.subheader("课程详情")
            for lesson in lessons:
                vocab_count = len(get_vocabulary_from_db(lesson[0]))
                st.write(f"**{lesson[1]}**：{vocab_count} 个单词")
        
        # ============ 管理员功能 ============
        elif menu == "⚙️ 管理课程":
            st.header("⚙️ 课程管理")
            
            tab1, tab2 = st.tabs(["查看课程", "添加课程"])
            
            with tab1:
                lessons = get_lessons_from_db()
                st.write(f"总共 **{len(lessons)}** 个课程")
                
                for lesson in lessons:
                    vocab_count = len(get_vocabulary_from_db(lesson[0]))
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.write(f"**{lesson[1]}** - {vocab_count}个单词 ({lesson[3]})")
                    with col2:
                        if st.button("🗑️", key=f"del_lesson_{lesson[0]}"):
                            success, msg = delete_lesson_from_db(lesson[0])
                            if success:
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)
            
            with tab2:
                st.subheader("添加新课程")
                new_title = st.text_input("课程名称 (例如：4️⃣ 颜色)")
                new_desc = st.text_area("课程描述 (例如：学习颜色词汇)")
                new_category = st.text_input("分类 (例如：描述)")
                new_level = st.selectbox("难度等级", ["初级", "中级", "高级"])
                
                if st.button("添加课程"):
                    if new_title:
                        success, lesson_id, msg = add_lesson_to_db(new_title, new_desc, new_category, new_level)
                        if success:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
                    else:
                        st.error("请输入课程名称")
        
        elif menu == "📝 管理词汇":
            st.header("📝 词汇管理")
            
            lessons = get_lessons_from_db()
            lesson_options = {f"{l[1]}": l[0] for l in lessons}
            
            selected_lesson_name = st.selectbox("选择课程", list(lesson_options.keys()))
            lesson_id = lesson_options[selected_lesson_name]
            
            tab1, tab2 = st.tabs(["查看词汇", "添加词汇"])
            
            with tab1:
                vocab_list = get_vocabulary_from_db(lesson_id)
                st.write(f"共 **{len(vocab_list)}** 个单词")
                
                for vocab in vocab_list:
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.write(f"**{vocab[2]}** ({vocab[4]}) - {vocab[3]}")
                    with col2:
                        if st.button("🗑️", key=f"del_vocab_{vocab[0]}"):
                            success, msg = delete_vocabulary_from_db(vocab[0])
                            if success:
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)
            
            with tab2:
                st.subheader("添加新词汇")
                new_arabic = st.text_input("阿拉伯语 (例如：أحمر)")
                new_english = st.text_input("英文 (例如：Red)")
                new_pronunciation = st.text_input("发音 (例如：Ahmar)")
                new_example = st.text_input("例子 (例如：颜色)")
                
                if st.button("添加词汇"):
                    if new_arabic and new_english:
                        success, msg = add_vocabulary_to_db(lesson_id, new_arabic, new_english, 
                                                           new_pronunciation, new_example)
                        if success:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
                    else:
                        st.error("请至少输入阿拉伯语和英文")
        
        elif menu == "📥 导入/导出":
            st.header("📥 数据导入/导出")
            
            tab1, tab2 = st.tabs(["导出数据", "导入数据"])
            
            with tab1:
                st.write("### 📊 导出所有课程和词汇")
                if st.button("生成导出文件"):
                    lessons_df, vocab_df = export_to_csv()
                    
                    # 下载课程
                    csv_lessons = lessons_df.to_csv(index=False, encoding='utf-8-sig')
                    st.download_button(
                        label="📥 下载课程列表.csv",
                        data=csv_lessons,
                        file_name="lessons.csv",
                        mime="text/csv"
                    )
                    
                    st.write("---")
                    
                    # 下载词汇
                    csv_vocab = vocab_df.to_csv(index=False, encoding='utf-8-sig')
                    st.download_button(
                        label="📥 下载词汇列表.csv",
                        data=csv_vocab,
                        file_name="vocabulary.csv",
                        mime="text/csv"
                    )
            
            with tab2:
                st.write("### 📤 导入词汇数据")
                
                st.info("""
                **CSV文件格式要求：**
                - 第一行必须是：arabic, english, pronunciation, example
                - 使用UTF-8编码保存
                - 分隔符必须是逗号 (,)
                
                **示例：**
                ```
                arabic,english,pronunciation,example
                أحمر,Red,Ahmar,颜色
                أزرق,Blue,Azraq,颜色
                أخضر,Green,Akhdar,颜色
                ```
                """)
                
                lessons = get_lessons_from_db()
                selected_lesson_name = st.selectbox("选择目标课程", 
                    [f"{l[1]}" for l in lessons], key="import_lesson")
                
                uploaded_file = st.file_uploader("选择CSV文件", type="csv")
                
                if uploaded_file and st.button("导入"):
                    success, msg = import_vocabulary_from_csv(uploaded_file, selected_lesson_name)
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
        
        elif menu == "📊 统计":
            st.header("📊 数据统计")
            
            lessons = get_lessons_from_db()
            total_vocab = sum(len(get_vocabulary_from_db(l[0])) for l in lessons)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("总课程数", len(lessons))
            with col2:
                st.metric("总词汇数", total_vocab)
            with col3:
                st.metric("平均/课", f"{total_vocab//len(lessons) if lessons else 0}")
            
            st.markdown("---")
            st.subheader("📈 课程详情")
            for lesson in lessons:
                vocab_count = len(get_vocabulary_from_db(lesson[0]))
                st.write(f"**{lesson[1]}**：{vocab_count} 个单词（{lesson[3]}）")

if __name__ == "__main__":
    main()
