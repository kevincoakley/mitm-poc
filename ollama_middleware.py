from flask import Flask, request, jsonify, make_response
from waitress import serve
import requests
import json
import os
import logging

# Create a Flask application instance
app = Flask(__name__)

# Configuration for the remote server
if "REMOTE_HOST" in os.environ:
    REMOTE_HOST = os.environ["REMOTE_HOST"]
else:
    REMOTE_HOST = "127.0.0.1"

if "REMOTE_PORT" in os.environ:
    REMOTE_PORT = int(os.environ["REMOTE_PORT"])
else:
    REMOTE_PORT = "11434"

# Configuration for the proxy server
FORBIDDEN_PATHS = ["/api/pull"]
API_KEY_SECRET = {"1234": "5678"}

# Flags for controlling print output for debugging
if "DEBUG" in os.environ:
    if os.environ["DEBUG"] == "True":
        DEBUG = True
    elif os.environ["DEBUG"] == "False":
        DEBUG = False
    else:
        DEBUG = True
else:
    DEBUG = True

PRINT_HEADERS = False
PRINT_REPONSE = False


def print_headers(headers):
    """Print all headers from the incoming request if PRINT_HEADERS is True."""
    app.logger.debug("Received Headers:")
    for key, value in headers.items():
        app.logger.debug(f"{key}: {value}")


def check_forbidden_paths(path):
    """Check if the requested path is forbidden and return an error response if so."""
    if path in FORBIDDEN_PATHS:
        return make_response(jsonify({"error": "Forbidden: Access denied"}), 403)
    return None


def validate_api_key():
    """Validate the API key and secret from the request headers, returning an error response if invalid."""
    api_key = request.headers.get("X-API-Key")
    api_secret = request.headers.get("X-API-Secret")

    if not api_key or not api_secret:
        return make_response(jsonify({"error": "Unauthorized: API key missing"}), 401)

    if api_key not in API_KEY_SECRET or API_KEY_SECRET.get(api_key) != api_secret:
        return make_response(jsonify({"error": "Forbidden: Invalid API key"}), 403)

    return None  # API key is valid


@app.route("/api/<path:path>", methods=["GET", "POST", "PUT", "DELETE"])
def proxy(path):
    """Proxy endpoint that handles all incoming requests, performing path and API key validation."""
    if PRINT_HEADERS:
        print_headers(request.headers)

    # Check for forbidden paths
    forbidden_response = check_forbidden_paths(request.path)
    if forbidden_response:
        return forbidden_response  # Return error response if path is forbidden

    # Validate API key
    validation_response = validate_api_key()
    if validation_response:
        return validation_response  # Return error response if API key validation fails

    # Forward the request to the actual API server
    return forward_request(path, request.headers.get("X-API-Key"))


def forward_request(path, api_key):
    """Forward the validated request to the actual API server and print the response if PRINT_RESPONSE is True."""
    url = f"http://{REMOTE_HOST}:{REMOTE_PORT}/api/{path}"
    headers = {key: value for key, value in request.headers.items() if key != "Host"}
    resp = requests.request(
        method=request.method,
        url=url,
        headers=headers,
        data=request.get_data(),
        params=request.args,
        allow_redirects=False,
    )

    if resp.status_code == 200:
        try:
            response_json = json.loads(resp.text)

            if PRINT_REPONSE:
                app.logger.debug(
                    f"Response JSON: {json.dumps(response_json, indent=2)}"
                )

            # Print API key and token counts if available
            app.logger.info(f"API Key: {api_key}")

            if "prompt_eval_count" in response_json:
                app.logger.info(
                    f"Input Token Count: {response_json['prompt_eval_count']}"
                )
            if "eval_count" in response_json:
                app.logger.info(f"Response Token Count: {response_json['eval_count']}")

        except json.JSONDecodeError:
            app.logger.error(f"Response is not valid JSON: {resp.text}")

    return resp.json(), resp.status_code


if __name__ == "__main__":

    if DEBUG:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO

    logging.basicConfig(level=log_level, format="%(asctime)s %(message)s")

    app.logger.info("Starting Ollama Proxy Server...")
    app.logger.info(f"Remote Host: {REMOTE_HOST}")
    app.logger.info(f"Remote Port: {REMOTE_PORT}")
    app.logger.info(f"Debug Mode: {DEBUG}")

    if DEBUG:
        app.run(debug=True, port=8080)
    else:
        serve(app, host="0.0.0.0", port=8080)
