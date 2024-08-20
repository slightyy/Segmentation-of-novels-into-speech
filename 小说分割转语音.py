import re
import pandas as pd
import edge_tts
import asyncio
from concurrent.futures import ThreadPoolExecutor
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import os

# 全局停止标志
stop_requested = False

# 全局变量chapters_list
chapters_list = []

# 读取TXT文件的内容
def read_txt_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            contents = file.read()
        return contents
    except UnicodeDecodeError:
        # 尝试使用GBK编码读取，这通常适用于中文Windows环境下的文件
        with open(file_path, 'r', encoding='gbk') as file:
            contents = file.read()
        return contents

# 更新后的分割小说为章节的函数
def split_novel_into_chapters(novel_content):
    # 包括阿拉伯数字和中文数字的正则表达式
    chapter_pattern = re.compile(r'第(?:[\d]+|[一二三四五六七八九十百千万零两]+)章')
    chapters = chapter_pattern.split(novel_content)
    chapter_titles = chapter_pattern.findall(novel_content)
    global chapters_list
    chapters_list = []
    for i in range(1, len(chapters)):
        chapter_title = chapter_titles[i-1].strip()
        chapter_content = chapters[i].strip()
        chapters_list.append((chapter_title, chapter_content))
    return chapters_list

# 异步生成音频文件
async def text_to_speech_edge_tts(data, voice):
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
        tasks = []
        for idx, row in data.iterrows():
            if stop_requested:
                break
            tasks.append(
                loop.run_in_executor(
                    executor,
                    generate_audio,
                    idx,
                    row['chapter_title'],
                    row['chapter_content'],
                    voice
                )
            )
        await asyncio.gather(*tasks)

def generate_audio(idx, title, content, voice):
    if stop_requested:
        return
    text = f"{title}。 {content}"
    communicator = edge_tts.Communicate(text, voice=voice)
    asyncio.run(communicator.save(f"chapter_{idx + 1}.mp3"))
    print(f"Generated chapter_{idx + 1}.mp3")

# 启动音频生成的独立线程
def start_audio_generation():
    global stop_requested
    stop_requested = False
    data = pd.DataFrame(chapters_list, columns=['chapter_title', 'chapter_content'])
    voice = voice_combobox.get()
    threading.Thread(target=lambda: asyncio.run(text_to_speech_edge_tts(data, voice))).start()
    messagebox.showinfo("音频生成", "音频文件生成中，请稍等...")

# 停止音频生成
def stop_audio_generation():
    global stop_requested
    stop_requested = True
    messagebox.showinfo("操作", "停止音频生成命令已发出。")

# 处理文件和生成音频的过程
def process_file():
    global chapters_list
    file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
    if file_path:
        novel_content = read_txt_file(file_path)
        chapters_list = split_novel_into_chapters(novel_content)
        messagebox.showinfo("文件处理", "TXT文件已读取并分章完成，可以开始生成音频。")

# 创建主窗口
root = tk.Tk()
root.title("小说TTS转换器")
root.geometry("400x300")  # 设置窗口大小

# 创建文件选择按钮
file_button = tk.Button(root, text="选择TXT文件", command=process_file)
file_button.pack(pady=10)

# 创建生成音频文件按钮
generate_button = tk.Button(root, text="生成音频文件", command=start_audio_generation)
generate_button.pack(pady=10)

# 创建停止生成音频文件按钮
stop_button = tk.Button(root, text="停止生成", command=stop_audio_generation)
stop_button.pack(pady=10)

# 创建语音选择下拉菜单
voice_label = tk.Label(root, text="选择语音:")
voice_label.pack(pady=5)

voice_options = [
    "zh-CN-XiaoxiaoNeural",
    "zh-CN-XiaoyiNeural",
    "zh-CN-YunjianNeural",
    "zh-CN-YunxiNeural",
    "zh-CN-YunxiaNeural",
    "zh-CN-YunyangNeural",
    "zh-CN-liaoning-XiaobeiNeural",
    "zh-CN-shaanxi-XiaoniNeural",
    "zh-HK-HiuGaaiNeural",
    "zh-HK-HiuMaanNeural",
    "zh-HK-WanLungNeural",
    "zh-TW-HsiaoChenNeural",
    "zh-TW-HsiaoYuNeural",
    "zh-TW-YunJheNeural"
]

voice_combobox = ttk.Combobox(root, values=voice_options, state="readonly")
voice_combobox.set(voice_options[0])
voice_combobox.pack(pady=5)

# 运行主循环
root.mainloop()
