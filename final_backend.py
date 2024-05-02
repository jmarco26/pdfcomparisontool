import difflib
import re
import fitz
import os

def extract_text(pdf_path):
    text = ""
    pdf = fitz.open(pdf_path)
    for page_num in range(len(pdf)):
        page = pdf.load_page(page_num)
        text += page.get_text()
    pdf.close()
    return text

with open('outputs/test_output_init.txt', 'w', encoding='utf-8') as f:
    string1 = extract_text('initial.pdf')
    f.write(string1)

with open('outputs/test_output_upd.txt', 'w', encoding='utf-8') as f:
    string2 = extract_text('updated.pdf')
    f.write(string2)

string1_list = string1.split()
string2_list = string2.split()

current_paragraph = []
added_strings = []
removed_strings = []

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

d = difflib.Differ()
diff = d.compare(string1_list, string2_list)

for line in diff:
    if line.startswith('- '):
        removed_strings.append(line[2:])
    elif line.startswith('+ '):
        added_strings.append(line[2:])
    else:
        current_paragraph.append(line[2:])

print(removed_strings)
print()
print(added_strings)


current_paragraph_str = ' '.join(current_paragraph)
added = find_and_append(added_strings, string2)
removed = find_and_append(removed_strings, string1)

added = re.sub(r'\s*\n+', '\n', added)
removed = re.sub(r'\s*\n+', '\n', removed)

removed = process_parenthesis(removed)

added, removed = double_compare(added, removed)

print()
print("Added Strings:",added)
print("\n\nRemoved Strings:", removed)

if not os.path.exists("output"):
    os.makedirs("output")
with open('outputs/final_output_text.txt', 'w') as f:
    f.write('[Added Lines/Paragraphs/Words]\n\n')
    f.write(added + '\n\n\n')
    f.write('[Removed Lines/Paragraphs/Words]\n\n')
    f.write(removed)
    f.close()