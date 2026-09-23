from flask import Flask, request, make_response, render_template_string

app = Flask(__name__)
FLAG = "TOH{c00k13s_l13_3v3ry_h4ll0w_3v3}"

PAGE = """
<html><body style="background:#0d0908;color:#f4e9df;font-family:sans-serif;text-align:center;padding:60px">
<h1>🕯️ The Witch's Ledger</h1>
<p>Role: {{ role }}</p>
{% if role == 'admin' %}
<p style="color:#ffb347">The ledger reveals: {{ flag }}</p>
{% else %}
<p style="color:#ff4d4d">Guests may not peek at the ledger.</p>
{% endif %}
</body></html>
"""

@app.route("/")
def index():
    role = request.cookies.get("role", "guest")
    resp = make_response(render_template_string(PAGE, role=role, flag=FLAG))
    if "role" not in request.cookies:
        resp.set_cookie("role", "guest")
    return resp

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
