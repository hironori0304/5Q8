import pandas as pd
import streamlit as st
import io
import random
from datetime import datetime
import matplotlib.pyplot as plt
import japanize_matplotlib  # 日本語フォントのサポートを追加
from io import BytesIO

def load_quiz_data(file):
    with io.TextIOWrapper(file, encoding='utf-8', errors='replace') as f:
        df = pd.read_csv(f)
    return df

def filter_and_sort_quiz_data(df, selected_years, selected_categories):
    if "すべて" in selected_years:
        selected_years = df['year'].unique().tolist()
    if "すべて" in selected_categories:
        selected_categories = df['category'].unique().tolist()
    
    # フィルタリング
    filtered_df = df[df['year'].isin(selected_years) & df['category'].isin(selected_categories)]
    
    # 分野ごとにソートし、リスト化する
    sorted_quizzes = []
    for category in selected_categories:
        category_df = filtered_df[filtered_df['category'] == category]
        for year in selected_years:
            year_df = category_df[category_df['year'] == year]
            sorted_quizzes.extend(year_df.to_dict('records'))
    
    quiz_data = []
    for quiz in sorted_quizzes:
        options = [quiz["option1"], quiz["option2"], quiz["option3"], quiz["option4"], quiz["option5"]]
        correct_option = quiz["answer"]
        shuffled_options = options[:]
        random.shuffle(shuffled_options)
        
        quiz_data.append({
            "question": quiz["question"],
            "options": shuffled_options,
            "correct_option": correct_option
        })
    
    return quiz_data

def generate_certificate_image(details, score, total_questions):
    # 証明書のサイズ設定
    fig, ax = plt.subplots(figsize=(10, 8))  # 幅10インチ、高さ8インチ
    ax.axis('off')

    # 「証明書」のタイトルを中央に表示
    ax.text(0.5, 0.8, "証明書", fontsize=36, ha='center', va='center', weight='bold')

    # その他の情報を左寄せで表示
    certificate_text = (
        f"氏名: {details['氏名']}\n\n"
        f"日付: {details['日付']}\n\n"
        f"過去問: {details['過去問']}\n\n"
        f"分野: {details['分野']}\n\n"
        f"問題数: {total_questions}問\n"
        f"正答数: {score}問\n"
        f"正答率: {details['accuracy_rate']:.2f}%\n"
    )
    ax.text(0.1, 0.4, certificate_text, fontsize=20, ha='left', va='top', wrap=True)

    # 画像をバッファに保存
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.5)
    buf.seek(0)
    plt.close(fig)
    return buf

def main():
    st.title("国家試験対策アプリ")

    if "quiz_data" not in st.session_state:
        st.session_state.quiz_data = []
    if "incorrect_data" not in st.session_state:
        st.session_state.incorrect_data = []
    if "current_quiz_data" not in st.session_state:
        st.session_state.current_quiz_data = []
    if "answers" not in st.session_state:
        st.session_state.answers = {}
    if "shuffled_options" not in st.session_state:
        st.session_state.shuffled_options = {}
    if "highlighted_questions" not in st.session_state:
        st.session_state.highlighted_questions = set()
    if "submit_count" not in st.session_state:
        st.session_state.submit_count = 0
    if "completed_problems" not in st.session_state:
        st.session_state.completed_problems = []

    uploaded_file = st.file_uploader("問題データのCSVファイルをアップロードしてください", type="csv")
    if uploaded_file is not None:
        try:
            df = load_quiz_data(uploaded_file)
            years = df['year'].unique().tolist()
            categories = df['category'].unique().tolist()

            years.insert(0, "すべて")
            categories.insert(0, "すべて")

            selected_years = st.multiselect("過去問の回数を選択してください", years)
            selected_categories = st.multiselect("分野を選択してください", categories)

            if selected_years and selected_categories:
                st.session_state.quiz_data = filter_and_sort_quiz_data(df, selected_years, selected_categories)
                st.session_state.current_quiz_data = st.session_state.quiz_data.copy()
                st.session_state.answers = {quiz["question"]: None for quiz in st.session_state.current_quiz_data}

            if st.session_state.current_quiz_data:
                for i, quiz in enumerate(st.session_state.current_quiz_data):
                    question_number = i + 1
                    is_highlighted = question_number in st.session_state.highlighted_questions
                    highlight_style = "background-color: #ffcccc;" if is_highlighted else ""

                    st.markdown(f"**<div style='padding: 10px; {highlight_style} font-size: 16px;'>問題 {question_number}</div>**", unsafe_allow_html=True)
                    st.markdown(f"<p style='margin-bottom: 0; font-size: 16px;'>{quiz['question']}</p>", unsafe_allow_html=True)

                    if quiz["question"] not in st.session_state.shuffled_options:
                        st.session_state.shuffled_options[quiz["question"]] = quiz["options"]
                    
                    options = st.session_state.shuffled_options[quiz["question"]]

                    selected_option = st.radio(
                        "",
                        options=options,
                        index=st.session_state.answers.get(quiz["question"], None),
                        key=f"question_{i}_radio"
                    )

                    if selected_option is not None:
                        st.session_state.answers[quiz["question"]] = selected_option

                    st.write("")  # 次の問題との間にスペースを追加

                name = st.text_input("氏名を入力してください")

                if st.button("回答"):
                    score = 0
                    total_questions = len(st.session_state.quiz_data)
                    incorrect_data = []
                    for i, quiz in enumerate(st.session_state.current_quiz_data):
                        correct_option = quiz["correct_option"]
                        selected_option = st.session_state.answers.get(quiz["question"], None)

                        is_correct = correct_option == selected_option

                        if is_correct:
                            score += 1
                            st.session_state.highlighted_questions.discard(i + 1)
                        else:
                            incorrect_data.append(quiz)
                            st.session_state.highlighted_questions.add(i + 1)

                    accuracy_rate = (score / total_questions) * 100
                    st.write(f"あなたのスコア: {score} / {total_questions}")
                    st.write(f"正答率: {accuracy_rate:.2f}%")

                    # 回答結果を保存
                    st.session_state.completed_problems.append({
                        "氏名": name,
                        "日付": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "過去問": ", ".join(selected_years),
                        "分野": ", ".join(selected_categories),
                        "問題数": total_questions,
                        "正答数": score,
                        "accuracy_rate": accuracy_rate
                    })

                # 証明書発行ボタン
                if st.button("証明書を発行"):
                    if st.session_state.completed_problems:
                        latest_problem = st.session_state.completed_problems[-1]
                        buf = generate_certificate_image(latest_problem, latest_problem["正答数"], latest_problem["問題数"])
                        st.image(buf, caption="証明書")
                        st.download_button(
                            label="証明書をダウンロード",
                            data=buf,
                            file_name="certificate.png",
                            mime="image/png"
                        )
                    else:
                        st.warning("証明書を発行するには、まず問題に回答してください。")

        except Exception as e:
            st.error(f"エラーが発生しました: {str(e)}")

if __name__ == "__main__":
    main()
