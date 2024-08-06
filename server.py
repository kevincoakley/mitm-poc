from http.server import BaseHTTPRequestHandler, HTTPServer
import http.client
import json

remote_host = "127.0.0.1"
remote_port = 11434
forbidden_paths = ["/api/pull"]
timeout = 600
print_headers = False
print_reponse = False


class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if print_headers:
            # Print the request headers
            self.print_headers()

        # Verify the API key is valid
        api_key = self.get_api_key()
        if api_key == -1:
            return

        # Forward the request to the target server
        self.forward_request(api_key=api_key)

    def do_POST(self):
        if print_headers:
            # Print the request headers
            self.print_headers()

        # Check for forbidden path
        if self.path in forbidden_paths:
            self.send_response(403)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"Forbidden: Access denied")
            return

        # Verify the API key is valid
        api_key = self.get_api_key()
        if api_key == -1:
            return

        # Read the body of the POST request if any
        content_length = int(self.headers.get("Content-Length", 0))
        post_body = self.rfile.read(content_length) if content_length else b""

        # Forward the request to the target server with the new body
        self.forward_request(api_key=api_key, body=post_body.decode("utf-8"))

    def do_HEAD(self):
        if print_headers:
            # Print the request headers
            self.print_headers()

        # Verify the API key is valid
        api_key = self.get_api_key()
        if api_key == -1:
            return

        # Forward the request to the target server
        self.forward_request(api_key=api_key)

    def print_headers(self):
        # Print the request headers
        for header, value in self.headers.items():
            print(f"{header}: {value}")

    def get_api_key(self):
        # Check if the API key is present in the headers
        if "Api-Key" not in self.headers:
            print("Unauthorized: API key missing")
            self.send_response(401)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"Unauthorized: API key missing")
            return -1

        # Check if the API key is valid
        if self.headers["Api-Key"] != "1234":
            print("Forbidden: Invalid API key")
            self.send_response(403)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"Forbidden: Invalid API key")
            return -1

        return self.headers["Api-Key"]

    def forward_request(self, api_key=None, body=None):
        # Determine the method and path
        method = self.command
        path = self.path

        try:
            # Establish a connection to the target server
            conn = http.client.HTTPConnection(remote_host, remote_port, timeout=timeout)

            # Prepare headers
            headers = {key: value for key, value in self.headers.items()}
            headers["Host"] = "%s:%s" % (remote_host, remote_port)

            # Send the request to the target server
            conn.request(method, path, body, headers)

            # Get the response from the target server
            response = conn.getresponse()

            # Read the response data
            response_data = response.read()
            response_text = response_data.decode("utf-8")

            # Parse response data as JSON if possible
            try:
                response_json = json.loads(response_text)

                # Print the response JSON
                if print_reponse:
                    print("Response JSON:", json.dumps(response_json, indent=2))

                # Print the token counts if available
                print("API Key:", api_key)
                if "prompt_eval_count" in response_json:
                    print("Input Token Count:", response_json["prompt_eval_count"])
                if "eval_count" in response_json:
                    print("Response Token Count:", response_json["eval_count"])

            except json.JSONDecodeError:
                print("Response is not valid JSON:", response_text)

            # Send the response back to the client
            self.send_response(response.status, response.reason)
            for header, value in response.getheaders():
                self.send_header(header, value)
            self.end_headers()
            self.wfile.write(response_data)

            # Close the connection
            conn.close()
        except Exception as e:
            self.send_response(502)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(f"Bad Gateway: {str(e)}".encode("utf-8"))


def run(server_class=HTTPServer, handler_class=RequestHandler, port=8080):
    server_address = ("", port)
    httpd = server_class(server_address, handler_class)
    httpd.timeout = timeout
    print(f"Starting httpd server on port {port}")
    httpd.serve_forever()


if __name__ == "__main__":
    run()
