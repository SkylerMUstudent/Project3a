from flask import Flask, render_template, request, redirect, url_for, Blueprint, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import requests
import pygal
import csv

app = Flask(__name__)
app.config["DEBUG"] = True
app.config["SECRECT_KEY"] = 'your secret key'
app.secret_key = 'your secret key'


#=========API Information==========
#API_KEY = '6P95RTQHO9NS644U' This is old key, I reached my limit of 25 daily uses.
API_KEY = 'ZGYRABMAZS9SGWI5' #this new key was an attempt to continue working, but it failed as well.
api_url = 'https://www.alphavantage.co/query'


#===========Functions===========
#This function pulls the list of symbols from the 'stocks.csv'
def get_symbols():
    symbol_list = []
    with open('stocks.csv', newline='') as csvfile:
        symbols = csv.DictReader(csvfile)
        for row in symbols:
            symbol_list.append(row['Symbol'])
    
    return symbol_list


#The function will create the chart the user wants
def create_chart(data, chart_type):
    sorted_data = dict(sorted(data.items()))

    dates = list(sorted_data.keys())

    prices = [float(info["4. close"]) for info in sorted_data.values()]

    if chart_type == "1":
        chart = pygal.Bar()
    else:
        chart = pygal.Line()

    chart.title = "Stock Data"
    chart.x_labels = dates
    chart.add("Close Price", prices)

    return chart.render_data_uri()


#========Appilcation views/routes=========
#This displays the main webpage.
@app.route('/', methods=['GET', 'POST'])
def index():
    chart = None
    symbol_list = get_symbols()

    if request.method == 'POST':
        symbol = request.form.get('symbol')
        chart_type = request.form.get('chart_type')
        time_series = request.form.get('time_series')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')

        user_input_time_series ={
            "1": "TIME_SERIES_INTRADAY",
            "2": "TIME_SERIES_DAILY",
            "3": "TIME_SERIES_WEEKLY",
            "4": "TIME_SERIES_MONTHLY"
        }

        time_series_list = user_input_time_series.get(time_series)

        if time_series_list == "TIME_SERIES_INTRADAY":
            interval = "5min"
        else:
            interval = None

        url = api_url
        params = {
            "function": time_series_list,
            "symbol": symbol,
            "apikey": API_KEY
        }

        if interval:
            params["interval"] = interval
        if start_date and end_date:
            params["datatype"] = "json"

        response = requests.get(url, params=params)
        data = response.json()

        time_series_key = next((key for key in data if "Time Series" in key), None)

        if not time_series_key:
            flash("Error: Could not get data. Please check inputs.", "error")
            return render_template("stocks.html", chart=None, symbol_list=symbol_list)

        time_series_data = data[time_series_key]

        start_time = datetime.strptime(start_date, "%Y-%m-%d")
        end_time = datetime.strptime(end_date, "%Y-%m-%d")

        filtered_data = {
            date: info for date, info in time_series_data.items()
            if start_time <= datetime.strptime(date, "%Y-%m-%d %H:%M:%S" if " " in date else "%Y-%m-%d") <= end_time
        }

        chart = create_chart(filtered_data, chart_type)

    return render_template("stocks.html", chart=chart, symbol_list=symbol_list)

if __name__ == "__main__":
    app.run(debug=True, port=5010, host="0.0.0.0")


#Make the Docker Image in Terminal
#docker-compose up -d