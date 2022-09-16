# Name: Maitreyee Damale
from datetime import date
import os
from sqlite3.dbapi2 import SQLITE_ALTER_TABLE
from flask import Flask, flash, redirect, render_template, request, url_for
import sqlite3
from werkzeug.utils import secure_filename
import pyodbc
import os
import plotly.graph_objs as go
import plotly.offline as plt
import plotly
import numpy as np
import json

from markupsafe import Markup

app = Flask(__name__)
print(os.getenv("PORT"))
port = int(os.getenv("PORT", 5000))

db = None
counter = 1
account_name = ""
account_key = ""
container_name = ""
connect_str = ''

def get_sql_connection():
    server = 'maitreyeedb.database.windows.net'
    database = ''
    username = ''
    password = ''
    cnxn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+password)
    return cnxn


def close_sql_connection(connection):
    connection.close()


@app.route('/')
def home():
   return render_template('homePage.html')

@app.route('/countMagnitude5', methods=['POST','GET'])
def countMagnitude5():
	if (request.method=='POST'):
		conn = get_sql_connection()
		cur = conn.cursor()
		sql= "select mag, time from all_month where mag > 5.0"
		cur.execute(sql)
		rows = cur.fetchall()
		print (repr(rows))
	return render_template('countMagnitude5.html', rows = rows)	


@app.route('/earthquakeMagnitudeRange', methods=['GET', 'POST'])
def earthquakeMagnitudeRange():
    if(request.method == 'POST'):
        conn = get_sql_connection()
        cur = conn.cursor()
        minMag = str(request.form['minMag'])
        maxMag = str(request.form['maxMag'])
        print("minimum mag: " + minMag)
        print("max mag: " + maxMag)
        startDate = str(request.form['startDate'])
        endDate = str(request.form['endDate'])
        print("End Date: " + endDate)
        query = "select mag, time, latitude, longitude, locationSource from all_month WHERE CAST(mag as INT) BETWEEN "+str(minMag)+" AND "+str(maxMag)+" AND time BETWEEN '"+str(startDate)+"' AND '"+str(endDate)+"'" 
        query1 = "select mag, DATEPART(time, date), latitude, longitude, locationSource from all_month WHERE CAST(mag as INT) BETWEEN "+str(minMag)+" AND "+str(maxMag)+" AND time BETWEEN '"+str(startDate)+"' AND '"+str(endDate)+"'" 
        print(query)
        cur.execute(query)
        rows = cur.fetchall()
        lat = []
        longi = []
        location = []
        mag = []
        datepart=[]
        for i in rows:
            lat.append(i[2])
            longi.append(i[3])
            location.append(i[4])
            mag.append(i[0])
            datepart.append(i[1])
        #print(repr(rows))
        fig = go.Figure(data=go.Scattergeo(
        lon = longi,
        lat = lat,
        text = location + mag,
        mode = 'markers',
        
        marker = dict(
            size = 8,
            opacity = 0.8,
            reversescale = True,
            autocolorscale = False,
            symbol = 'square',
            line = dict(
                width=1,
                color='rgba(102, 102, 102)'
            ),
            colorscale = 'Blues',
            cmin = min(mag),
            color = mag,
            cmax = max(mag),
            colorbar_title="Earthquakes <br>Magnitude Range"
        )))



        fig.update_layout(
            title = 'Earthquakes in given date range',
            geo = dict(
                scope='usa',
                projection_type='albers usa',
                showland = True,
                landcolor = "rgb(250, 250, 250)",
                subunitcolor = "rgb(217, 217, 217)",
                countrycolor = "rgb(217, 217, 217)",
                countrywidth = 0.5,
                subunitwidth = 0.5
            ),
        )
        fig_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
        

        trace1 = {
            "type": "scatter",
            "mode": "lines",
            "name": 'Magintude vs time',
            "x": datepart,
            "y": mag,
            "line": {'color': '#17BECF'}
            }
        data = [go.Scatter(trace1)]
        
        layout=go.Layout(title='Time Series with Rangeslider',xaxis=dict(autorange = True, range=[startDate,endDate]),yaxis=dict(autorange = True,range = [int(minMag), int(maxMag)],type='linear'))
        tfig = go.Figure(data=data, layout=layout)
        tfig_json = json.dumps(tfig, cls=plotly.utils.PlotlyJSONEncoder)
        print(tfig_json)

    return render_template('earthquakeMagnitudeRange.html', plot = Markup(fig_json), tplot = Markup(tfig_json))


@app.route('/earthquakeLocation', methods=['GET', 'POST'])
def earthquakeLocation(latitude=None,longitude=None,radius=None):
    if(request.method == 'POST'):
        conn = get_sql_connection()
        cur = conn.cursor()
        latitude = float(request.form['lat'])
        longitude = float(request.form['long'])
        radius = float(request.form['radius'])
        lat1 = latitude-(radius/111)
        lat2 = latitude+(radius/111)
        long1 = longitude-(radius/111)
        long2 = longitude+(radius/111)
        query = "SELECT * from all_month WHERE latitude > '"+str(lat1)+"' and latitude < '"+str(lat2)+"' and longitude > '"+str(long1)+"' and longitude < '"+str(long2)+"'"
        print(query)
        cur.execute(query)                          
        rows = cur.fetchall()
        print(repr(rows))
    return render_template('earthquakeLocation.html', rows = rows)


@app.route('/countMagnitude4', methods=['GET', 'POST'])
def countMagnitude4():
    if(request.method == 'POST'):
        conn = get_sql_connection()
        cur = conn.cursor()       
        query ="SELECT count(*) from all_month WHERE mag > 4.0 and DATEPART( HOUR,time) >= 18 OR DATEPART( HOUR,time) <= 6"
        print(query)
        cur.execute(query)
        rows = cur.fetchall()
        print(repr(rows))
    return render_template('countMagnitude4.html', rows = rows)


@app.route('/clusters', methods=['GET', 'POST'])
def clusters():
    if(request.method == 'POST'):
        conn = get_sql_connection()
        cur = conn.cursor()
        field= str(request.form['mag2'])
        print(field)
        query = "SELECT locationSource,COUNT(locationSource) AS 'no. of earthquakes' FROM all_month where mag > '"+str(field)+"' GROUP BY locationSource"
        print("Printing query")
        print(query)
        cur.execute(query)
        rows = cur.fetchall()
        print (repr(rows))
        x_axis = []
        y_axis = []
        for res in rows:
            x_axis.append(res[0])
            y_axis.append(res[1])
        
        #print(x_axis)

        trace1 = go.Bar(x=x_axis, y=y_axis)
        layout = go.Layout(title="No. of Earthquakes by location of mag > "+ str(field), xaxis=dict(title="Location"),
                        yaxis=dict(title="No. of Earthquakes", dtick=100, automargin = True),width=900 )
        data = [trace1]
        fig = go.Figure(data=data, layout=layout)
        fig_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
        figP =go.Figure(data=[go.Pie(labels=x_axis, values=y_axis)])
        figP_json = json.dumps(figP, cls=plotly.utils.PlotlyJSONEncoder)
        
    return render_template("visuals.html", plot=Markup(fig_json), plotP = Markup(figP_json))



if __name__ == '__main__':
    app.run()
