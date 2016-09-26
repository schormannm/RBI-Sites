@app.route("/output/download", methods=["POST"])
@login_required
def output_download():
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
        print sites
        # site_data = fill_site_data(doc)
        # sites.append(site_data)

        filename = save_to_workbook(sites)
        send_from_directory(directory='/home/mark/PycharmProjects/RBI-Sites/', filename=filename)
        return render_template("output.html", searchform=form, sites=sites)
    else:
        print "Form failed to validate"

    return redirect(url_for('output'))


def output_download_old():
    file = open('result.in','r')
    # print file
    #    file = request.files['data_file']
    if not file:
        return "No file"

    file_contents = file.read().decode("utf-8")

    result = transform(file_contents)

    response = make_response(result)
    response.headers["Content-Disposition"] = "attachment; filename=result.csv"
    return response


def transform(text_file_contents):
    return text_file_contents.replace("=", ",")


@app.route('/output/download/<path:filename>', methods=['GET', 'POST'])
def download(filename):
    return send_from_directory(directory='/home/mark/PycharmProjects/RBI-Sites/', filename=filename)
