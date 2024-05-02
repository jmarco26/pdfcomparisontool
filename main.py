import tkinter as tk
from tkinter import filedialog, scrolledtext
from pdfminer.high_level import extract_text
import re
import difflib
from bs4 import BeautifulSoup

#window functions--------------------------------------------------------
def create_frame(root, bg_color):
    frame = tk.Frame(root, bg=bg_color)
    frame.pack(side='left', fill='both', expand=True)
    return frame

def modify_textwidget(text_widget, frame):
    scrollbar = tk.Scrollbar(frame, orient='vertical', command=text_widget.yview)
    text_widget.config(yscrollcommand=scrollbar.set, bg='white') 
    text_widget.pack(side='top', fill='both', expand=True, padx=20, pady=20)
    text_widget.config(state='disabled')
#window functions---------------------------------------------------------

def extract_from_pdf(pdf_path):
    text = extract_text(pdf_path)
    return text

def extract_paragraphs_from_pdf(pdf_path):
    text = extract_from_pdf(pdf_path)
    paragraphs = re.split('\n\n', text)
    return paragraphs

def generate_html(paragraphs):
    html = "<!DOCTYPE html>\n<html>\n<head>\n<title>PDF to HTML</title>\n</head>\n<body>\n"

    for paragraph in paragraphs:
        html += f"\n<p>\n{paragraph.strip()}\n</p>\n"

    html += "</body>\n</html>"

    return html

def save_html(html_content, output_path):
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

def open_file(text_widget, label):
    file_path = filedialog.askopenfilename(filetypes=[('PDF files', '*.pdf')])
    if file_path:
        text = extract_from_pdf(file_path)
        text_widget.config(state='normal') 
        text_widget.delete('1.0', tk.END) 
        text_widget.insert('1.0', text)                                                             
        text_widget.config(state='disabled') 
        label.config(text=file_path) 

def generate_and_save_html(label1, label2):
    file_path1 = label1.cget("text")
    file_path2 = label2.cget("text")

    file_name1 = file_path1.split('/')[-1].split('.')[0]
    file_name2 = file_path2.split('/')[-1].split('.')[0]

    paragraphs1 = extract_paragraphs_from_pdf(file_path1)
    paragraphs2 = extract_paragraphs_from_pdf(file_path2)

    html_content1 = generate_html(paragraphs1)
    html_content2 = generate_html(paragraphs2)

    output_path1 = f"{file_name1}_main(OLD).html"
    output_path2 = f"{file_name2}_main(NEW).html"
    save_html(html_content1, output_path1)
    save_html(html_content2, output_path2)

    compare_and_save_output(output_path1, output_path2)   

def compare_and_save_output(output_path1, output_path2):
    with open(output_path1, 'r', encoding='utf-8') as f:
        html_content1 = f.read()

    with open(output_path2, 'r', encoding='utf-8') as f:
        html_content2 = f.read()

    soup1 = BeautifulSoup(html_content1, 'html.parser')
    soup2 = BeautifulSoup(html_content2, 'html.parser')

    paragraphs1 = [p.get_text() for p in soup1.find_all('p')]
    paragraphs2 = [p.get_text() for p in soup2.find_all('p')]

    diff_output = []
    differ = difflib.Differ()
    diff = list(differ.compare(paragraphs1, paragraphs2))
    with open("RAW_OUTPUT.txt", 'w', encoding='utf-8') as f:
        f.write(''.join(diff))

    for line in diff:
        if line.startswith('-'):
            pass
        else:
            line = re.sub(r'\-{2,}', '<deleted>', line)
            line = re.sub(r'\+{2,}', '<updated>', line)
            line = re.sub(r'\^+|\+ |\?|\+\n', '', line)
            diff_output.append(line.strip())

    output_text = '\n'.join(diff_output)
    with open("OUTPUT_COMPARISON.txt", 'w', encoding='utf-8') as f:
        f.write(output_text)
    display_comparison(output_text)

def display_comparison(output_text):
    comparison_window = tk.Toplevel()
    comparison_window.title("Comparison Result")

    comparison_text = scrolledtext.ScrolledText(comparison_window)
    comparison_text.pack(fill="both", expand=True)

    comparison_text.insert(tk.END, output_text)

    comparison_text.config(state="disabled")

root = tk.Tk()
root.title('PDF Comparative Tool')
root.geometry('1400x850')

#window objects-------------------------------------------------------------
frame1 = create_frame(root, 'steelblue')
frame2 = create_frame(root, 'lightskyblue')

text_box1 = scrolledtext.ScrolledText(frame1)
modify_textwidget(text_box1, frame1)
text_box2 = scrolledtext.ScrolledText(frame2)
modify_textwidget(text_box2, frame2)

label1 = tk.Label(frame1, text="", bg='steelblue')  
label1.pack()
label2 = tk.Label(frame2, text="", bg='lightskyblue') 
label2.pack()

open_btn1 = tk.Button(frame1, text='Open OLD PDF', command=lambda: open_file(text_box1, label1))
open_btn1.pack(side='left', anchor='s', pady=10, padx=20)

open_btn2 = tk.Button(frame2, text='Open UPDATED PDF', command=lambda: open_file(text_box2, label2))
open_btn2.pack(side='left', anchor='s', pady=10, padx=20)

compare_btn = tk.Button(frame2, text='Compare PDF', command=lambda: generate_and_save_html(label1, label2))
compare_btn.pack(side='right', anchor='s', pady=10, padx=20)
root.mainloop()
#window objects--------------------------------------------------------------