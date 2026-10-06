from flask import Flask, request, jsonify, send_from_directory
import threading
import traceback
import os

# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")


# ============================================================
# FLASK APP
# ============================================================

app = Flask(
    __name__,
    static_folder=FRONTEND_DIR,
    static_url_path=""
)


# ============================================================
# AUTOMATION STATUS
# ============================================================

automation_status = {
    "running": False,
    "status": "Ready",
    "message": "Waiting to start automation.",
    "processed": 0,
    "submitted": 0,
    "errors": 0,
    "current_page": 0,
    "total_pages": 0,
    "current_proposal": "",
}


# ============================================================
# SERVE FRONTEND
# ============================================================

@app.route("/")
def home():

    return send_from_directory(
        FRONTEND_DIR,
        "index.html"
    )


# ============================================================
# AUTOMATION WORKER
# ============================================================

def automation_worker(username, password):

    global automation_status

    try:

        automation_status.update({
            "running": True,
            "status": "Running",
            "message": "Starting COSMOS automation...",
            "processed": 0,
            "submitted": 0,
            "errors": 0,
            "current_page": 0,
            "total_pages": 0,
            "current_proposal": "",
        })

        # ----------------------------------------------------
        # IMPORT YOUR PLAYWRIGHT AUTOMATION
        # ----------------------------------------------------

        from automation import run_automation


        # ----------------------------------------------------
        # RUN PLAYWRIGHT
        # ----------------------------------------------------

        run_automation(
            username=username,
            password=password,
            status=automation_status
        )


        # ----------------------------------------------------
        # COMPLETED
        # ----------------------------------------------------

        automation_status.update({
            "running": False,
            "status": "Completed",
            "message": "Automation completed successfully.",
            "current_proposal": "",
        })


    except Exception as e:

        print("\n" + "=" * 70)
        print("AUTOMATION ERROR")
        print("=" * 70)

        traceback.print_exc()

        automation_status.update({
            "running": False,
            "status": "Error",
            "message": str(e),
            "current_proposal": "",
        })


# ============================================================
# START AUTOMATION
# ============================================================

@app.route(
    "/api/start",
    methods=["POST"]
)
def start_automation():

    global automation_status


    # --------------------------------------------------------
    # DON'T START TWO AUTOMATIONS
    # --------------------------------------------------------

    if automation_status["running"]:

        return jsonify({
            "success": False,
            "message": "Automation is already running."
        }), 409


    # --------------------------------------------------------
    # GET JSON FROM FRONTEND
    # --------------------------------------------------------

    data = request.get_json(
        silent=True
    )


    if not data:

        return jsonify({
            "success": False,
            "message": "No data received."
        }), 400


    username = data.get(
        "username",
        ""
    ).strip()

    password = data.get(
        "password",
        ""
    )


    # --------------------------------------------------------
    # VALIDATE
    # --------------------------------------------------------

    if not username:

        return jsonify({
            "success": False,
            "message": "Username is required."
        }), 400


    if not password:

        return jsonify({
            "success": False,
            "message": "Password is required."
        }), 400


    # --------------------------------------------------------
    # START BACKGROUND THREAD
    # --------------------------------------------------------

    thread = threading.Thread(
        target=automation_worker,
        args=(
            username,
            password,
        ),
        daemon=True
    )

    thread.start()


    return jsonify({
        "success": True,
        "message": "Automation started."
    })


# ============================================================
# GET AUTOMATION STATUS
# ============================================================

@app.route(
    "/api/status",
    methods=["GET"]
)
def get_status():

    return jsonify(
        automation_status
    )


# ============================================================
# STOP
# ============================================================

@app.route(
    "/api/stop",
    methods=["POST"]
)
def stop_automation():

    # --------------------------------------------------------
    # IMPORTANT
    #
    # We are NOT force-killing Playwright here.
    #
    # First version keeps this safe.
    # We can later add a proper stop_event.
    # --------------------------------------------------------

    if not automation_status["running"]:

        return jsonify({
            "success": False,
            "message": "Automation is not running."
        })


    return jsonify({
        "success": False,
        "message": (
            "Stop control is not enabled yet. "
            "Automation will continue."
        )
    })


# ============================================================
# RUN FLASK
# ============================================================

if __name__ == "__main__":

    print("=" * 70)
    print("COSMOS AUTOMATION SERVER")
    print("=" * 70)

    print()
    print("Frontend:")
    print("http://127.0.0.1:5000")

    print()
    print("Starting server...")
    print()

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False,
        threaded=True
    )