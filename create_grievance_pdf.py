from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
import textwrap

def create_grievance_pdf():
    c = canvas.Canvas("05_grievance_meena.pdf", pagesize=letter)
    width, height = letter
    
    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(72, height - 72, "GRIEVANCE PETITION")
    
    # Recipient
    c.setFont("Helvetica", 12)
    c.drawString(72, height - 120, "To,")
    c.drawString(72, height - 140, "The District Agriculture Officer")
    c.drawString(72, height - 160, "Auraiya District")
    c.drawString(72, height - 180, "Uttar Pradesh")
    
    # Subject
    c.setFont("Helvetica-Bold", 12)
    c.drawString(72, height - 220, "Subject: COMPLAINT REGARDING DELAY IN SUBSIDY PAYMENT")
    
    # Body content
    c.setFont("Helvetica", 11)
    body_text = """Respected Sir/Madam,

I am Meena Devi, a resident of village Chandpur, tehsil Konch, district Auraiya. 
I am writing to bring to your kind attention the issue of delayed subsidy payment.

I had applied for the Crop Insurance Scheme on 15th June 2023 for the Kharif season. 
My application number is INS-UP-2023-789012. The premium amount of Rs. 2,500 was paid 
through my bank account (SBI, Account No. 1234567890123456).

As per the scheme guidelines, the subsidy amount was to be credited within 30 days 
of application processing. However, it has been more than 8 months now, and I have 
not received any payment. I have made repeated inquiries at the local agriculture 
office, but no satisfactory response has been provided.

Due to this delay, I am facing financial difficulties in arranging resources for 
the current Rabi season. The delayed payment is causing significant hardship 
for my family.

I request your kind intervention to resolve this matter urgently and ensure 
that the pending subsidy payment is released at the earliest.

Thank you for your attention to this important matter.

Sincerely,
Meena Devi
Mobile: 9123456789
Aadhaar: 345678901234
Date: 20/02/2024

URGENT ATTENTION REQUIRED - PENDING FOR 8 MONTHS"""
    
    # Wrap text and draw
    lines = textwrap.wrap(body_text, width=70)
    y_position = height - 260
    for line in lines:
        c.drawString(72, y_position, line)
        y_position -= 15
        if y_position < 72:  # Start new page if needed
            c.showPage()
            y_position = height - 72
    
    c.save()
    print("PDF created: 05_grievance_meena.pdf")

if __name__ == "__main__":
    create_grievance_pdf()
