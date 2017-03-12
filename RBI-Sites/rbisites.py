import datetime
import os
import sys
import string
import json
import time
import re
import urllib2
import dateparser
from collections import OrderedDict

from flask import Flask
from flask import render_template
from flask import make_response
from flask import request
from flask import jsonify
from flask.ext.login import LoginManager
from flask.ext.login import login_required
from flask.ext.login import login_user
from flask.ext.login import logout_user
from flask.ext.login import current_user
from flask import send_file

from flask import redirect
from flask import url_for
from flask import send_from_directory
from flask import Response

from passwordhelper import PasswordHelper
from user import User
from bitlyhelper import BitlyHelper

from forms import RegistrationForm
from forms import LoginForm
from forms import SearchForm
from forms import UpdateForm
from forms import DateForm

from myutils import sanitize_string
from myutils import format_date

import config

from workbook_output import save_to_workbook

if config.test:
    from mockdbhelper import MockDBHelper as DBHelper
else:
    from dbhelper import DBHelper


DB = DBHelper()
PH = PasswordHelper()
BH = BitlyHelper()

app = Flask(__name__)
login_manager = LoginManager(app)
app.secret_key = 'dbQsAFFNGnugJ4Zmv1YJeCj4btAofOn3/Y2/iRsgA7/UvKvEJqb29NWFBvzMzRNR1xGTb0xbJZBrW+xrcCOTn7xIJBbNoIbY88Y'


@app.route("/")
def home():
    return render_template("home.html", loginform=LoginForm(), registrationform=RegistrationForm())


@app.route("/new-user")
def register_new_user():
    now = datetime.datetime.now()
    return render_template("register_new_user.html", registrationform=RegistrationForm())


@login_manager.user_loader
def load_user(user_id):
    user_password = DB.get_user(user_id)
    if user_password:
        return User(user_id)


@app.route("/login", methods=["POST"])
def login():
    form = LoginForm(request.form)
    if form.validate():
        stored_user = DB.get_user(form.loginemail.data)
        if stored_user and PH.validate_password(form.loginpassword.data, stored_user['salt'], stored_user['hashed']):
            user = User(form.loginemail.data)
            login_user(user, remember=True)
            return redirect(url_for('dashboard'))
        form.loginemail.errors.append("Email or password invalid")
    return render_template("home.html", loginform=form, registrationform=RegistrationForm())


@app.route("/register", methods=["POST"])
def register():
    form = RegistrationForm(request.form)
    print "About to validate form"
    if form.validate():
        print "Validated"
        if DB.get_user(form.email.data):
            form.email.errors.append("Email address already registered")
            return render_template("home.html", loginform=LoginForm(), registrationform=form)
        print "User is not already in database - so good to add"
        salt = PH.get_salt()
        hashed = PH.get_hash(form.password2.data + salt)
        DB.add_user(form.email.data, salt, hashed)
        return render_template("home.html", loginform=LoginForm(), registrationform=form,
                               onloadmessage="Registration successful. Please log in.")
    return render_template("register_new_user.html", loginform=LoginForm(), registrationform=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("home"))


@app.route("/dashboard")
@login_required
def dashboard():
    nownow = datetime.datetime.now().strftime('%Y-%m-%d')
    lattice_cnt = DB.get_site_count({"site.tower_type": "Lattice"})
    lattice_cnt += DB.get_site_count({"site.tower_type": "lattice"})
    monopole_cnt = DB.get_site_count({"site.tower_type": "Monopole"})
    monopole_cnt += DB.get_site_count({"site.tower_type": "monopole"})
    monolattice_cnt = DB.get_site_count({"site.tower_type": "Mono-Lattice"})
    monolattice_cnt += DB.get_site_count({"site.tower_type": "mono lattice"})
    rooftop_cnt = DB.get_site_count({"site.tower_type": "Roof top"})
    rooftop_cnt += DB.get_site_count({"site.tower_type": "rooftop"})
    total_cnt = DB.get_site_count({})
    other_cnt = total_cnt - rooftop_cnt - monolattice_cnt - lattice_cnt - monopole_cnt
    context = {
        'features': [
            {'description': 'Lattice', 'value': lattice_cnt},
            {'description': 'Monopole', 'value': monopole_cnt},
            {'description': 'Mono-Lattice', 'value': monolattice_cnt},
            {'description': 'Rooftop', 'value': rooftop_cnt},
            {'description': 'Other or none', 'value': other_cnt},
            {'description': 'Total', 'value': total_cnt},
        ], 'date_now': nownow
    }
    return render_template("dashboard.html", **context)


@app.route("/dashboard/resolve")
@login_required
def dashboard_resolve():
    request_id = request.args.get("request_id")
    DB.delete_request(request_id)
    return redirect(url_for('dashboard'))


@app.route("/update")
@login_required
def update():
    return render_template("update.html", searchform=SearchForm())


@app.route("/edit")
@login_required
def edit():
    return render_template("edit.html", searchform=SearchForm())


@app.route("/edit/search", methods=["POST"])
@login_required
def edit_search():
    form = SearchForm(request.form)
    print form.data
    if form.validate():
        query = make_query(site_name=form.site_name.data,
                           site_number=form.site_number.data,
                           region=form.region.data,
                           type=form.tower_type.data,
                           date_of_inspection=form.date_of_inspection.data
                           )
        sites = DB.find_sites(query)
        return render_template("edit.html", searchform=form, sites=sites)
    return redirect(url_for('edit'))


def fix_xonomy(content):
    print content
    content = content.replace('\n', '')
    content = content.replace('\r', '')
    content = content.replace('"', "'")
    return content


@app.route("/edit/showsite", methods=["POST", "GET"])
@login_required
def edit_showsite():
    siteid = request.args.get("siteid")
    sites = list(DB.get_site_byID(siteid))
    assert (len(sites) == 1), "More than 1 site with same site ID"
    site = sites[0]
    print site
    raw_file = site["site"]["meta"]["file_name"]
    if not os.path.exists(raw_file):
        return redirect(url_for('edit'))        # could use an alternate URL for better feedback
    with open(raw_file, 'r') as content_file:
        content = content_file.read()
    content = fix_xonomy(content)
    return render_template("edit-site.html", file_content=content, file=raw_file,  siteid=siteid)


@app.route("/edit/save", methods=['GET', 'POST'])
@login_required
def edit_save():
    siteid = request.form["siteid"]
    updated_xml = request.form['updatedXML']
    xml = updated_xml.replace("xml:space='preserve'", "")
    raw_file = request.form['raw_file']
    print "Data received : " + xml
    print "Output file : " + raw_file
    print "Site id : " + siteid
    with open(raw_file, 'w') as content_file:
        content_file.write(xml)
    sites = list(DB.get_site_byID(siteid))
    assert (len(sites) == 1), "More than 1 site with same site ID"
    site = sites[0]
    print site
    DB.update_site_edited(siteid, True)
    return redirect(url_for('edit'))


@app.route("/update/search", methods=["POST"])
@login_required
def update_search():
    form = SearchForm(request.form)
    print form.data
    if form.validate():
        query = make_query(site_name=form.site_name.data,
                           site_number=form.site_number.data,
                           region=form.region.data,
                           type=form.tower_type.data,
                           date_of_inspection=form.date_of_inspection.data
                           )
        sites = DB.find_sites(query)
        return render_template("update.html", searchform=form, sites=sites)
    return redirect(url_for('update'))


@app.route("/update/showsite", methods=["POST", "GET"])
@login_required
def update_showsite():
    siteid = request.args.get("siteid")
    form = UpdateForm()

    if DB.check_manual_exists(siteid):  # has previously been updated
        print "Inside /lookup/showsite - and DB.manual_exists is True"
        sites = list(DB.show_site(siteid))
        mysite = sites[0]
        manual = mysite['site']['manual']
        form.site_classification.data = manual['site_classification']
        form.site_release_date.data = manual['site_release_date']
        form.as_built_available.data = manual['as_built_available']
        form.fault_description.data = manual['fault_description']
        form.mast_engineer.data = manual['mast_engineer']
        form.mast_upgraded.data = manual['mast_upgraded']
        form.mast_upgraded_date.data = manual['mast_upgraded_date']
        form.capacity_top.data = manual['capacity_top']
        form.capacity_10_from_top.data = manual['capacity_10_from_top']
    else:                               # not previously updated - add the fields
        print "Inside /lookup/showsite - and DB.manual_exists is False"
        context = {
            'site.manual.updated': 'False',
            'site.manual.site_classification': "",
            'site.manual.site_release_date': "",
            'site.manual.as_built_available': "",
            'site.manual.fault_description': "",
            'site.manual.mast_engineer': "",
            'site.manual.mast_upgraded': "",
            'site.manual.mast_upgraded_date': "",
            'site.manual.capacity_top': "",
            'site.manual.capacity_10_from_top': "",
            'site.manual.update_date': ""
        }
        DB.update_site_manual(siteid, context)
    sites = list(DB.get_site_byID(siteid))
    assert (len(sites) == 1), "More than 1 site with same site ID"
    site = sites[0]
    print site
    return render_template("update-site.html", updateform=form, site=site)


@app.route("/update/save", methods=['GET','POST'])
@login_required
def update_save():
    # siteid = request.args.get("siteid")
    form = UpdateForm(request.form)
    siteid = form.siteid.data
    print form.data
    print "Inside lookup/update - about to validate form"
    print siteid
    print form.site_classification.data
    nownow = datetime.datetime.now().strftime('%Y-%m-%d')
    if form.validate():
        context = {
            'site.manual.updated': 'True',
            'site.manual.site_classification': form.site_classification.data,
            'site.manual.site_release_date': form.site_release_date.data,
            'site.manual.as_built_available': form.as_built_available.data,
            'site.manual.fault_description': form.fault_description.data,
            'site.manual.mast_engineer': form.mast_engineer.data,
            'site.manual.mast_upgraded': form.mast_upgraded.data,
            'site.manual.mast_upgraded_date': form.mast_upgraded_date.data,
            'site.manual.capacity_top': form.capacity_top.data,
            'site.manual.capacity_10_from_top': form.capacity_10_from_top.data,
            'site.manual.update_date': nownow
        }
        DB.update_site_manual(siteid, context)
        sites = list(DB.show_site(siteid))
        site = sites[0]
        print "Show site after fetch"
        print site
        # return render_template("update-site.html", updateform=form, site=site)
    return redirect(url_for('update'))


@app.route("/compare")
@login_required
def compare():
    return render_template("compare.html", searchform=SearchForm())


@app.route("/output")
@login_required
def output():
    return render_template("output.html", searchform=SearchForm())


@app.route("/output/search", methods=["POST"])
@login_required
def output_search():
    form = SearchForm(request.form)
    if form.validate():
        query = make_query(
            site_name=form.site_name.data,
            site_number=form.site_number.data,
            region=form.region.data,
            type=form.tower_type.data,
            date_of_inspection=form.date_of_inspection.data
        )

        sites = list(DB.find_sites(query))

        main_filename = save_to_workbook(sites, "sites.xlsx")

        # loading_filename = save_to_workbook(sites, output_columns_loadings, "loadings.xlsx")

        return render_template('download.html')
    else:
        print "Form failed to validate"
        return render_template("output.html", searchform=SearchForm())


@app.route('/download-file/')
@login_required
def output_download():
    try:
        filename = "sites.xlsx"
        parentddir = os.path.abspath(os.path.dirname(__file__))
        full_path = os.path.join(parentddir, filename)
        out_filename = "sites_out.xlsx"
        # send_from_directory(directory=parentddir, filename=filename)
        return send_file(full_path, attachment_filename=out_filename, as_attachment=True)
    except Exception as e:
        return str(e)


@app.route('/VC-download/')
def VC_download():
    return "Happy days"


@app.route('/VC-download/login')
def VC_download_login():
    return "Fat chance of that working"


@app.route('/VC-download/list', methods=["POST", "GET"])
def VC_download_list():
    site_name  = request.args.get("site_name")
    site_number = ''
    region = ''
    tower_type = ''
    date_of_inspection = ''
    print site_name
    query = make_query(site_name=site_name,
                       site_number=site_number,
                       region=region,
                       type=tower_type,
                       date_of_inspection=date_of_inspection
                       )
    projection = make_projection()
    sites = DB.find_sites(query, projection)
    sites_list = []
    for site in sites:
        sites_list.append(site["site"])
    return jsonify({'site_list': sites_list})


@app.route('/VC-download/fetch/<string:uuid>')
def VC_download_fetch(uuid):
    site = DB.get_site_byUUID(uuid)
    site_body = site["site"]
    return jsonify({'Site': site_body})


def make_projection(site_name=True, site_number=True, region=True, type=True, date_of_inspection=True, uuid=True):
    projection = {}
    if site_name:
        projection['site.site_group.site_name'] = '1'
    if site_number:
        projection['site.site_group.site_number'] = '1'
    if region:
        projection['site.site_group.region'] = '1'
    if type:
        projection['site.tower_type'] = '1'
    if date_of_inspection:
        projection['site.date_of_inspection'] = '1'
    if uuid:
        projection['site.@instanceID'] = '1'

    return projection

def make_query(site_name=None, site_number=None, region=None, type=None, date_of_inspection=None):
    # all queries begin with something common, which may be an empty dict, but here's an example
    query = {}

    if site_name:
        clean_str = site_name.strip(" ")
        regexp = re.compile(clean_str, re.IGNORECASE)
        query['site.site_group.site_name'] = regexp
    if site_number:
        clean_str = site_number.strip(" ")
        regexp = re.compile(clean_str, re.IGNORECASE)
        query['site.site_group.site_number'] = regexp
    if region:
        query['site.site_group.region'] = region
    if type:
        query['site.tower_type'] = type
    if date_of_inspection:
        query['site.date_of_inspection'] = date_of_inspection
    # etc...

    return query


@app.route('/vort', methods=['post', 'get'])
def vort():
    form = DateForm()
    if form.validate_on_submit():
        print form.dt.data
        return form.dt.data.strftime('%Y-%m-%d')
    return render_template('vort.html', form=form)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='10.240.221.76', port=port, debug=True)
