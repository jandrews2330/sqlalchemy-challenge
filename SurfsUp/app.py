# Import the dependencies.
from flask import Flask, jsonify
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

import datetime as dt


#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(autoload_with=engine)


# Save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station

# Create our session (link) from Python to the DB
session = Session(engine)

#################################################
# Flask Setup
#################################################
app = Flask(__name__)



#################################################
# Flask Routes
#################################################
# Homepage route
@app.route("/")
def welcome():
    return (
        f"<h1>Welcome to the Hawaii Climate API</h1>"
        f"<h3>Available Routes:</h3>"
        f"<ul>"
        f"<li>/api/v1.0/precipitation</li>"
        f"<li>/api/v1.0/stations</li>"
        f"<li>/api/v1.0/tobs</li>"
        f"<li>/api/v1.0/&lt;start&gt;</li>"
        f"<li>/api/v1.0/&lt;start&gt;/&lt;end&gt;</li>"
        f"</ul>"
    )

# Precipitation route
@app.route("/api/v1.0/precipitation")
def precipitation():
    # Most recent date in dataset
    recent_date = session.query(func.max(Measurement.date)).scalar()
    one_year_ago = dt.datetime.strptime(recent_date, '%Y-%m-%d') - dt.timedelta(days=365)

    # Query for the last 12 months of precipitation data
    results = session.query(Measurement.date, Measurement.prcp).\
        filter(Measurement.date >= one_year_ago).all()

    # Convert to dictionary (date: prcp)
    precip_data = {date: prcp for date, prcp in results}
    return jsonify(precip_data)

# Stations route
@app.route("/api/v1.0/stations")
def stations():
    results = session.query(Station.station).all()
    stations_list = [station[0] for station in results]
    return jsonify(stations_list)

# Temperature observations from most active station
@app.route("/api/v1.0/tobs")
def tobs():
    # Most recent date and one year ago
    recent_date = session.query(func.max(Measurement.date)).scalar()
    one_year_ago = dt.datetime.strptime(recent_date, '%Y-%m-%d') - dt.timedelta(days=365)

    # Find most active station
    most_active_station = session.query(Measurement.station).\
        group_by(Measurement.station).\
        order_by(func.count().desc()).first()[0]

    # Query temperature observations for last 12 months from most active station
    results = session.query(Measurement.date, Measurement.tobs).\
        filter(Measurement.station == most_active_station).\
        filter(Measurement.date >= one_year_ago).all()

    # Format as list of dicts
    tobs_list = [{date: temp} for date, temp in results]
    return jsonify(tobs_list)

# Start date route (TMIN, TAVG, TMAX from start)
@app.route("/api/v1.0/<start>")
@app.route("/api/v1.0/<start>/<end>")
def temperature_stats(start, end=None):
    # Create select statement
    sel = [
        func.min(Measurement.tobs),
        func.avg(Measurement.tobs),
        func.max(Measurement.tobs)
    ]

    # Conditional logic depending on whether end date is provided
    if end:
        results = session.query(*sel).filter(Measurement.date >= start).filter(Measurement.date <= end).all()
    else:
        results = session.query(*sel).filter(Measurement.date >= start).all()

    # Unpack result tuple
    temps = results[0]
    temp_summary = {
        "Start Date": start,
        "End Date": end if end else "Latest",
        "TMIN": temps[0],
        "TAVG": round(temps[1], 2),
        "TMAX": temps[2]
    }

    return jsonify(temp_summary)

if __name__ == "__main__":
    app.run(debug=True)