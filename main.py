import tkinter as tk
from tkinter import filedialog, scrolledtext
import fitz
import difflib
import re
from PIL import Image, ImageTk

current_paragraph = []
added_strings = []
removed_strings = []

def create_frame(root, bg_color, side):
    frame = tk.Frame(root, bg=bg_color)
    frame.pack(side=side, fill='both', expand=True)
    return frame
#-----------------------------------------------------------------
def extract_from_pdf(pdf_path):
    text = ''
    pdf = fitz.open(pdf_path)
    for page_num in range(len(pdf)):
        page = pdf.load_page(page_num)
        text += page.get_text()
    pdf.close()
    return text
#-----------------------------------------------------------------
def initialization(label1, label2):
    file_path1 = label1.cget("text")
    file_path2 = label2.cget("text")

    file_name1 = file_path1.split('/')[-1].split('.')[0]
    file_name2 = file_path2.split('/')[-1].split('.')[0]

    paragraphs1 = extract_from_pdf(f'{file_name1}.pdf')
    paragraphs2 = extract_from_pdf(f'{file_name2}.pdf')

    paragraphs1 = ''.join(paragraphs1)
    paragraphs2 = ''.join(paragraphs2)


    new_added, new_removed = compare(paragraphs1, paragraphs2)

    display_comparison(new_added, new_removed)

#-----------------------------------------------------------------
def display_comparison(added_words, removed_words):
    output_text = ('[Added Lines/Paragraphs/Words]\n\n' + added_words + '\n\n\n'
                   + '[Removed Lines/Paragraphs/Words]\n\n' + removed_words)

    comparison_window = tk.Toplevel()
    comparison_window.title("Comparison Result")

    comparison_text = scrolledtext.ScrolledText(comparison_window)
    comparison_text.pack(fill="both", expand=True)

    comparison_text.insert(tk.END, output_text)

    comparison_text.config(state="disabled")
#------------------------------------------------------------------
def compare(string1, string2):

    d = difflib.Differ()
    differ = d.compare(string1.split(), string2.split())
    for line in differ:
        if line.startswith('- '):
            removed_strings.append(line[2:])
        elif line.startswith('+ '):
            added_strings.append(line[2:])
        else:
            current_paragraph.append(line[2:])
    added = find_and_append(added_strings, string2)
    removed = find_and_append(removed_strings, string1)

    added = re.sub(r'\s*\n+', '\n', added)
    removed = re.sub(r'\s*\n+', '\n', removed)

    added = process_parenthesis(added)
    removed = process_parenthesis(removed)

    added, removed = double_compare(added, removed)

    return added, removed
#-----------------------------------------------------------------
def find_and_append(find_list, line):
    temp_result = ""
    result = ""
    words = line.splitlines()
    words = line.splitlines()
    open_parenthesis_count=0

    for sublist in words[:]:
        for word in find_list[:]:
            if word not in sublist:
                temp_result += '\n'
                break
            if word in sublist:
                if '(' in word and ')' in word:
                    temp_result += word + ' '
                    find_list.remove(word)
                elif '(' in word:
                    open_parenthesis_count += 1
                    temp_result += word + ' '
                    find_list.remove(word)
                elif ')' in word:
                    open_parenthesis_count -= 1
                    temp_result += word + '\n'
                    find_list.remove(word)
                    break
                elif open_parenthesis_count > 0:
                    temp_result += word + ' '
                    find_list.remove(word)
                else:
                    temp_result += word + ' '
                    find_list.remove(word)
        words.remove(sublist)
    result += ''.join(temp_result)
    return result
#----------------------------------------------------------------
def double_compare(new, deleted):
    new = re.sub(r'-\s?\n?', '-', new)
    deleted = re.sub(r'-\s?\n?', '-', deleted)
    new_list = new.splitlines()
    deleted_list = deleted.splitlines()
    new_result = ''
    deleted_result = ''
    deleted_string = re.sub(r'\n+', ' ', deleted)
    new_string = re.sub(r'\n+', ' ', new)

    for new_line in new_list:
        if new_line not in deleted_string:
            new_result += new_line + '\n'
            continue
    for deleted_line in deleted_list:
        if deleted_line not in new_string:
            deleted_result += deleted_line + '\n'
            continue

    return new_result, deleted_result
#-----------------------------------------------------------------
def process_parenthesis(words):
    word_list = words.splitlines()
    result = ''
    open_parenthesis_count = 0
    for word in word_list[:]:
        if '(' in word and ')' in word:
            result += word + '\n'
            word_list.remove(word)
        elif '(' in word:
            open_parenthesis_count += 1
            result += word
            word_list.remove(word)
        elif ')' in word:
            open_parenthesis_count -= 1
            result += word + '\n'
            word_list.remove(word)
        elif open_parenthesis_count > 0:
            result += word
            word_list.remove(word)
        else:
            result += word + '\n'
            word_list.remove(word)
    return result
#-----------------------------------------------------------------
def open_file(canvas, label):
    file_path = filedialog.askopenfilename(filetypes=[('PDF files', '*.pdf')])
    if file_path:
        doc = fitz.open(file_path)
        images = []
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            pix = page.get_pixmap()
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            images.append(img)
            #print(f"Image loaded for canvas {canvas} from page {page_num + 1}")
        doc.close()
        
        canvasImg = Image.new("RGB", (images[0].width, sum(img.height for img in images)))
        y_offset = 0
        for img in images:
            canvasImg.paste(img, (0, y_offset))
            y_offset += img.height
        canvasImg_ref = ImageTk.PhotoImage(canvasImg)
        if canvas == '1':
            canvas1.create_image(0, 0, anchor=tk.NW, image=canvasImg_ref)
            canvas1.image = canvasImg_ref  
            #print("Image displayed on canvas 1")
        elif canvas == '2':
            canvas2.create_image(0, 0, anchor=tk.NW, image=canvasImg_ref)
            canvas2.image = canvasImg_ref  
            #print("Image displayed on canvas 2")
    label.config(text=file_path)
#-----------------------------------------------------------------
#binding scroll wheel for viewing pdf contents per canvas
def on_mouse_wheel(event):
    canvas = event.widget
    if canvas.bbox("all")[3] > canvas.winfo_height():
        scroll_amount = -1 * (event.delta // 120)
        
        canvas.yview_scroll(scroll_amount, "units")
#-----------------------------------------------------------------        
root = tk.Tk()
root.title('PDF Comparing Tool')
root.geometry('1400x850')

frame1 = create_frame(root, 'steelblue', 'left')
frame2 = create_frame(root, 'lightskyblue', 'right')

canvas1 = tk.Canvas(frame1, bg='white', width=400, height=600)
canvas1.pack(side='top', fill='both', expand=True, pady=20, padx=20)
canvas2 = tk.Canvas(frame2, bg='white', width=400, height=600)
canvas2.pack(side='top', fill='both', expand=True, pady=20, padx=20)

label1 = tk.Label(frame1, text="", bg='steelblue')  
label1.pack()
label2 = tk.Label(frame2, text="", bg='lightskyblue') 
label2.pack()

open_btn1 = tk.Button(frame1, text='Open OLD PDF', command=lambda: open_file('1', label1))
open_btn1.pack(side='left', anchor='s', pady=10, padx=20)

open_btn2 = tk.Button(frame2, text='Open UPDATED PDF', command=lambda: open_file('2', label2))
open_btn2.pack(side='left', anchor='s', pady=10, padx=20)

compare_btn = tk.Button(frame2, text='Compare PDF', command=lambda: initialization(label1, label2))
compare_btn.pack(side='right', anchor='s', pady=10, padx=20)

canvas1.bind('<MouseWheel>', on_mouse_wheel)
canvas2.bind('<MouseWheel>', on_mouse_wheel)

root.mainloop()
