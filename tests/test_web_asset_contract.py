import re


def test_index_template_uses_single_css_and_module_entry(client):
    response = client.get("/")
    assert response.status_code == 200

    html = response.get_data(as_text=True)
    stylesheet_links = re.findall(r'<link[^>]+href="([^"]+)"', html)
    module_scripts = re.findall(r'<script[^>]+type="module"[^>]+src="([^"]+)"', html)
    classic_scripts = re.findall(r'<script(?![^>]+type="module")[^>]+src="([^"]+)"', html)

    assert stylesheet_links == ["/static/css/style.css"]
    assert module_scripts == ["/static/js/modules/main.js?v=4.10"]
    assert classic_scripts == []
