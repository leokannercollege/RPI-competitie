from flask import Flask, render_template, request, g, redirect, session, url_for
import json
import pandas as pd
import segno

from PIL import Image
import io
import os
import glob

application = app = Flask(__name__)

@app.before_request
def before_request():
    g.user = None
    if 'user_id' in session:
        user = [x for x in users if x.id == session['user_id']][0]
        g.user = user        

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session.pop('user_id', None)       

        username = request.form.get('email')
        password = request.form.get('password')

        user = [x for x in users if x.username == username]

        if user and user[0].password == password:        
            session['user_id'] = user[0].id
            return redirect(url_for('home'))

        return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/home')
def home():
    if not g.user:
        return redirect(url_for('login')) 
    return render_template('product.html', login=True)

@app.route('/product', methods=['POST', 'GET'])
def new_product():
    product = {}

    if not g.user:
        return redirect(url_for('login'))

    elif request.method == 'POST':
        
        form = request.form

        #Product gets added
        if "submit" in request.form:
            total_score = (0.7 * float(form['energie'])+ 0.3 * (float(form['arbeid'])+float(form['water'])+ \
                float(form['co2'])+float(form['stikstof'])+float(form['dieren'])/5))/2

            with open("db_products.json", "r") as f:
                data = json.load(f)

            with open("db_products.json", "w") as f:                  
                product = {
                    "producent":form['producent'],
                    "artikel":form['artikel'],
                    "ean_code":form['ean'],		    
                    "schone energie": form['energie'],
                    "arbeidsomstandigheden": form['arbeid'], 
                    "waterverbruik": form['water'],
                    "CO2-uitstoot": form['co2'],
                    "stikstofuitstoot": form['stikstof'],
                    "dierenwelzijn": form['dieren'],
                    "totaal": total_score #rounding it to the nearest integer
                    #rounding it up if total_score > 5 otherwise we're rounding it down.
                    #unlike the ceil() and floor() functions
                }            

                data.append(product) 
                link = "http://" + request.host + '/product/' + str(len(data))
                br = '\n'
                star = '⭐'  

                qr_string = (
                    f"Producent: {product['producent']}{br}"
                    f"Artikel: {product['artikel']}{br}"            
                    f"Schone energie {star*int(form['energie'])}{br}"
                    f"Arbeidsomstandigheden {star*int(form['arbeid'])}{br}"
                    f"Waterverbruik {star*int(form['water'])}{br}"
                    f"CO\u2082-uitstoot {star*int(form['co2'])}{br}"
                    f"Stikstofuitstoot {star*int(form['stikstof'])}{br}"
                    f"Dierenwelzijn {star*int(form['dieren'])}{br}{br}"
                    f"Totaal score {star*int(round(total_score))}{br}"
                    f"\u24D8Meer informatie:{br}"
                    f"{link}"
                )              

                #print(qr_string)
                qrcode = segno.make_qr(qr_string)         
                qrcode.save(f'static/images/{len(data)}.png', scale=10)

                #Loading the image into memory instead of writing to disk immediately
                out = io.BytesIO()
                qrcode.save(out, scale=10, kind="png")
                out.seek(0)

                img = Image.open(out)

                img = img.resize((300,300))

                #screen coordinate orgin is in the top left corner
                paste_cords = (50, 0)
                #creating a new image and pasting the old one on top of it
                #The "Inky What" screen we're using expects an image to be 400 by 300 pixels
                screen_img = Image.new("RGB", (400,300), color=(255,255,255))
                screen_img.paste(img, paste_cords)

                #The "Inky What requires a highly specific color pallete"
                #(White, Black, Red)
                #Hence why we're having to convert our image from RGB to this custom palette
                pallete = Image.new("P", (1, 1))
                pallete.putpalette((255, 255, 255, 0, 0, 0, 255, 0, 0) + (0, 0, 0) * 252)

                screen_img = screen_img.convert("RGB").quantize(palette=pallete)

                screen_img.save(f"static/images/{len(data)}.png")

                #Saving the data back into the database
                json.dump(data, f, indent=4)
        
        #database gets purged
        elif "clean" in request.form:
            #clean json
            with open("db_products.json", "w") as w:
                #setting it back to an empty array
                json.dump([], w, indent=4)

            #Please make sure that this is the right path
            files = glob.glob("static/images/*")
            for f in files:
                os.remove(f)
    
    return render_template('product.html', login=True) 

@app.route('/products')
def show_products():
    if not g.user:
        return redirect(url_for('login'))

    with open("db_products.json", "r") as f:
        data = json.load(f)
    print(data)
    df_products = pd.DataFrame.from_records(data)
    df_products = df_products.to_html(classes= "table table-striped", justify="center").replace('<td>', '<td align="center">')      
    return render_template('products.html', products= df_products, login=True)

@app.route('/product/<int:num>')
def detail_information(num):
    found = True    
    with open("db_products.json", "r") as f:
        data = json.load(f)

    if len(data) < num:
        found = False
    else:
        product = data[num-1]

    return render_template('product_details.html', product=product, error=found)


@app.route('/logout')
def logout():
    g.user = None
    session.clear()    
    return redirect(url_for('login'))

@app.route("/databasesize401", methods=["POST", "GET"])
def return_database_size():
    with open("db_products.json", "r") as r:
        data = json.load(r)
        return str(len(data))

class User:
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

    def __repr__(self):
        return f'<User: {self.username}>'

users = []

with open("config.json", "r") as f:
    config = json.load(f)

    for user in config:
        users.append(User(id=1, username=user["username"], password=user["password"]))

if __name__ == '__main__':        
    application.config['SECRET_KEY'] = 'LKCtesting 123'
    application.run(host='0.0.0.0' , debug=True)
