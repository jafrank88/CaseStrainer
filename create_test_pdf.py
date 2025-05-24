from fpdf import FPDF
import os


def create_test_pdf():
    # Create test_files directory if it doesn't exist
    os.makedirs("test_files", exist_ok=True)

    # Read the text file
    with open("test_files/test.txt", "r") as f:
        text = f.read()

    # Create PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Add text to PDF
    for line in text.split("\n"):
        pdf.cell(200, 10, txt=line, ln=True)

    # Save PDF
    pdf.output("test_files/test.pdf")
    print("PDF created successfully at test_files/test.pdf")


if __name__ == "__main__":
    create_test_pdf()
