from flask import Flask, render_template
from flask_wtf import Form
from wtforms import DateField
from datetime import date

app = Flask(__name__)
app.secret_key = 'SHH!'


class DateForm(Form):
    dt = DateField('Pick a Date', format="%m/%d/%Y")


@app.route('/', methods=['post', 'get'])
def home():
    form = DateForm()
    if form.validate_on_submit():
        mydate = form.dt.data
        print mydate
        return form.dt.data.strftime('%Y-%m-%d')
    return render_template('vort.html', form=form)


if __name__ == '__main__':
    app.run(debug=True)
