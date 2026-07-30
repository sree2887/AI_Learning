from openai import OpenAI
import PyPDF2
import tkinter as tk
from tkinter import filedialog

# ---------------------------
# PDF TEXT EXTRACTION
# ---------------------------
def extract_text_from_pdf(file_path):
    text = ""
    with open(file_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            text += page.extract_text() + "\n"
    return text

# ---------------------------
# OPENAI CLIENT
# ---------------------------
client = OpenAI()

def ask_about_document(document_text, question):
    response = client.responses.create(
        model="gpt-4o-mini",
        input=[
            {"role": "system", "content": "You are a helpful assistant who answers questions about documents."},
            {"role": "user", "content": f"Document text:\n{document_text}"},
            {"role": "user", "content": f"Question: {question}"}
        ]
    )
    return response.output_text

# ---------------------------
# FILE PICKER
# ---------------------------
def pick_pdf_file():
    root = tk.Tk()
    root.withdraw()  # hide the empty Tkinter window
    file_path = filedialog.askopenfilename(
        title="Select a PDF file",
        filetypes=[("PDF Files", "*.pdf")]
    )
    return file_path

# ---------------------------
# MAIN PROGRAM
# ---------------------------
if __name__ == "__main__":
    print("\nPlease choose a PDF file from the file picker window...")
    file_path = pick_pdf_file()

    if not file_path:
        print("No file selected. Exiting.")
        exit()

    print(f"\nSelected file: {file_path}")

    question = input("\nWhat do you want to ask about this document?\n> ")

    text = extract_text_from_pdf(file_path)
    answer = ask_about_document(text, question)

    print("\nAnswer:", answer)