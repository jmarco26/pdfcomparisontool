import tkinter as tk
from tkinter import filedialog
import fitz  # PyMuPDF
import re
import difflib
import webbrowser

class PDFFileComparer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PDF File Comparer")

        self.original_pdf_file = None
        self.updated_pdf_file = None

        self.original_pdf_label = tk.Label(self, text="Original PDF File:")
        self.original_pdf_label.grid(row=0, column=0, padx=10, pady=5)

        self.original_pdf_name_label = tk.Label(self, text="")
        self.original_pdf_name_label.grid(row=0, column=1, padx=10, pady=5)

        self.original_pdf_button = tk.Button(self, text="Select Original PDF", command=self.select_original_pdf)
        self.original_pdf_button.grid(row=0, column=2, padx=10, pady=5)

        self.updated_pdf_label = tk.Label(self, text="Updated PDF File:")
        self.updated_pdf_label.grid(row=1, column=0, padx=10, pady=5)

        self.updated_pdf_name_label = tk.Label(self, text="")
        self.updated_pdf_name_label.grid(row=1, column=1, padx=10, pady=5)

        self.updated_pdf_button = tk.Button(self, text="Select Updated PDF", command=self.select_updated_pdf)
        self.updated_pdf_button.grid(row=1, column=2, padx=10, pady=5)

        self.compare_button = tk.Button(self, text="Compare PDF Files and View Result", command=self.compare_pdf_files)
        self.compare_button.grid(row=2, column=1, padx=10, pady=5)
    
    #get the orig file
    def select_original_pdf(self):
        original_pdf_file_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if original_pdf_file_path:
            self.original_pdf_file = original_pdf_file_path
            self.original_pdf_name_label.config(text=original_pdf_file_path)
    
    #get the changed/updated file
    def select_updated_pdf(self):
        updated_pdf_file_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if updated_pdf_file_path:
            self.updated_pdf_file = updated_pdf_file_path
            self.updated_pdf_name_label.config(text=updated_pdf_file_path)

    #compare PDFs
    def compare_pdf_files(self):
        if self.original_pdf_file and self.updated_pdf_file:
            print("Comparing PDF Files:")
            print("Original PDF:", self.original_pdf_file)
            print("Updated PDF:", self.updated_pdf_file)
            
            #extract pdf
            def extract_text(pdf_path):
                text = ""
                pdf = fitz.open(pdf_path)
                for page_num in range(len(pdf)):
                    page = pdf.load_page(page_num)
                    text += page.get_text() + "---(((page"+str(page_num+1)+")))+++ \n" #extract text and add page counter
                pdf.close()
                text = text.replace("\n\u00A0\n","\n").replace("\u00A0"," ").replace("\n\n\n","\n").replace("\n\n","\n").replace("\n ","\n")
                text = text.replace("    "," ").replace("   "," ").replace("  "," ")
                text = re.sub(r'(\d[\)]?\s)\n',r'\1 ',text)
                text = text.replace("\u00A0"," ").replace("\n", " ").replace("\\x", " ").replace("    "," ").replace("   "," ").replace("  "," ")
                text = text.replace("- ","-")
                return text
            
            #clean the extracted text
            def clean_text(text):
                text = re.sub(r'-{3}\({3}page\d+\){3}\+{3}\s',r'',text) #remove page counter
                return text
            
            #compare texts by words
            def comp(initText, chanText):
                differ = difflib.Differ()
                diff = list(differ.compare(initText.split(), chanText.split()))
                return diff
            
            #combine the same texts
            def append_alikes(main_list):
                i = 0
                while i < len(main_list) - 1:
                    line = main_list[i]
                    nextLine = main_list[i+1]
                    if line[:2] == nextLine[:2]:
                        main_list[i] = line + nextLine[1:]
                        main_list.pop(i+1)  #remove the next line
                    else:
                        i += 1  #move to the next iteration if no merge occurs
                return main_list
            
            #find a string if it exists in the raw extracted initial texts
            def test_text(strings, referencesStr):
                if strings in re.sub(r'-{3}\({3}page\d+\){3}\+{3}\s',r'',referencesStr):
                    return True
                else:
                    return False

            extracted_initial = extract_text(self.original_pdf_file)
            extracted_changed = extract_text(self.updated_pdf_file)
            
            initial_text = clean_text(extracted_initial)
            changed_text = clean_text(extracted_changed)
            
            diff = comp(initial_text,changed_text)
            diff = append_alikes(diff)

            removedTpl = list()
            newStr = str()
            
            testDiff = list(diff)

            #get REMOVED TEXTS and NEW TEXTS
            i = 0
            while i < len(testDiff)-1:
                line = testDiff[i]
                nextLine = testDiff[i+1]
                temp_length = int(len(line[2:])-1)
                if line.startswith("+"):
                    if nextLine.startswith("?"):
                        testDiff.pop(i+1)
                    if not test_text(line[2:],initial_text):
                        newStr += line[2:] + "\n"
                    testDiff.pop(i)
                    testDiff = append_alikes(testDiff)
                    i = 0
                elif line.startswith("-") and nextLine.startswith(" "):
                    length = len(nextLine[2:])-1
                    if length > 25:
                        length = 25
                    removedTpl.append(("","",nextLine[2:length],line[2:]))
                    testDiff.pop(i+1)
                    testDiff.pop(i)
                    testDiff = append_alikes(testDiff)
                    i = 0
                elif line.startswith(" ") and nextLine.startswith("-"):
                    if temp_length > 100:
                        temp_length = 100
                    removedTpl.append((line[-temp_length:],nextLine[2:]))
                    testDiff.pop(i+1)
                    testDiff.pop(i)
                    testDiff = append_alikes(testDiff)
                    i = 0
                else:
                    i += 1

            pdfIn = fitz.open("ManCommFutAct_VER022024_OLD.pdf") #open the newer version of pdf
                        
            def addhighlight(strings, strokeTuple):
                
                def highlight(string, strokeTpl):
                    text_instances = list()
                    for page in pdfIn:
                        text_instances = page.search_for(string)
                        if text_instances:
                            for inst in text_instances:
                                annot = page.add_highlight_annot(inst)
                                annot.set_colors(stroke=strokeTpl)
                                annot.set_opacity(0.5)
                                annot.update()
                            break
                    if not text_instances:
                        maxLen = len(string)
                        if maxLen >= 180:
                            sixtySix = int(maxLen * 0.33)
                            string = string[sixtySix:]
                            highlight(string, strokeTpl)
                            
                for liness in strings.splitlines():
                    if liness.startswith("+") or liness.startswith("-"):
                        liness = liness[2:]
                    if liness.endswith(" "):
                        liness = liness[:-1]
                    highlight(liness, strokeTuple)
                
            addhighlight(newStr,(0,1,0)) #highlight new words as green

            def add_text_on_search(search_texts):
                for page_num in range(len(pdfIn)):
                    page = pdfIn[page_num]
                    page.clean_contents()

                    for search_text_tuple in search_texts:
                    
                        if len(search_text_tuple) == 2:  
                            search_text, text_to_add = search_text_tuple
                            is_top_placement = False
                        elif len(search_text_tuple) == 4: 
                            search_text, text_to_add = search_text_tuple[2], search_text_tuple[3]
                            is_top_placement = True  
                        else:
                            continue 

                        search_results = page.search_for(search_text)

                        if search_results:
                            result = search_results[0]
                            page_width = page.rect.width
                            text_lines = [text_to_add[i:i+100] for i in range(0, len(text_to_add), 100)]
                            if is_top_placement:
                                rect = fitz.Rect(60, result.y0 - 30, page_width, result.y0)
                            else:
                                text_box_height = max(len(text_lines), 60) * 15 
                                rect = fitz.Rect(60, result.y1 + 8, page_width - 60, result.y1 + text_box_height)

                            for line_num, line in enumerate(text_lines):
                                if line_num == 0:
                                    page.insert_textbox(rect, line, fontsize=11, color=(1, 0, 0))
                                else:
                                    rect.y0 += 15
                                    rect.y1 += 15
                                    page.insert_textbox(rect, line, fontsize=11, color=(1, 0, 0))

            add_text_on_search(removedTpl) # search texts which removed texts are beside them

            pdfIn.save("outputPDF.pdf")
            pdfIn.close() 
            webbrowser.open("outputPDF.pdf")
            #self.destroy()

        else:
            print("Please select both original and updated PDF files.")

if __name__ == "__main__":
    app = PDFFileComparer()
    app.mainloop()