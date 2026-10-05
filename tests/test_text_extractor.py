from app.services.text_extractor import extract_metadata, extract_visible_text


def test_extracts_metadata_and_removes_noise():
    html = """<html><head><title> Acme  Finance </title>
    <meta name="description" content="Business services"></head><body>
    <nav><svg>Noise</svg>Navigation</nav><script>malicious()</script>
    <style>body{color:red}</style><noscript>Enable JS</noscript>
    <div hidden>Hidden</div><span style="display: none">Secret</span>
    <main>Acme &amp; partners <p> Public information. </p></main>
    <footer>Footer noise</footer></body></html>"""
    page = extract_metadata(html)
    assert page.title == "Acme Finance"
    assert page.meta_description == "Business services"
    assert page.visible_text == "Acme & partners Public information."


def test_limits_text_and_accepts_malformed_html():
    assert len(extract_visible_text("<p>" + "x" * 1000, 100)) == 100
    assert extract_visible_text("") == ""


def test_nested_hidden_styles():
    assert (
        extract_visible_text(
            '<div style="display:none"><span style="color:red">hidden</span></div><p>Visible</p>'
        )
        == "Visible"
    )
