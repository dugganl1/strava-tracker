from flask import Flask, render_template

from strava_client import format_activity_for_receipt, get_activities

app = Flask(__name__)


@app.route("/")
def show_latest_receipt():
    activities = get_activities(limit=1)
    if activities:
        activity_data = format_activity_for_receipt(activities[0])
        return render_template("index.html", activity=activity_data)
    return "No recent activities found", 404


if __name__ == "__main__":
    app.run(debug=True)
