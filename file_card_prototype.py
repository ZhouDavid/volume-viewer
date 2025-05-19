from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = "supersecret"  # Needed for flash messages

# 6 example cards
cards = [
    {"id": "card1", "title": "Report.pdf", "date": "Uploaded on 2025-05-18"},
    {"id": "card2", "title": "Summary.docx", "date": "Uploaded on 2025-05-19"},
    {"id": "card3", "title": "Data.csv", "date": "Uploaded on 2025-05-20"},
    {"id": "card4", "title": "Presentation.pptx", "date": "Uploaded on 2025-05-21"},
    {"id": "card5", "title": "Notes.txt", "date": "Uploaded on 2025-05-22"},
    {"id": "card6", "title": "Image.png", "date": "Uploaded on 2025-05-23"},
]

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        clicked = request.form.get('card')
        for card in cards:
            if clicked == card["id"]:
                flash(f"{card['title']} clicked! You can add your custom logic here.")
        return redirect(url_for('index'))
    return render_template('card.html', cards=cards)

if __name__ == '__main__':
    app.run(debug=True)