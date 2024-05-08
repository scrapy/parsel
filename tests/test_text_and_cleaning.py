from lxml.html.clean import Cleaner

from parsel import Selector

HTML_BODY = """
<body>
    <div class="product">
        <div class="name">Product1</div>
        <span class="price"><b>Price:</b>100</span>
    </div>
    <div class="product">
        <div class="name">Product2</div>
        <span class="price"><b>Price:</b>200</span>
    </div>
</body>
"""


def test_text_get() -> None:
    sel = Selector("<p>title:<h1>some text</h1></p>")
    txt = sel.get(text=True)
    assert txt == "title:\n\nsome text"


def test_text_getall() -> None:
    sel = Selector("<ul><li>option1</li><li>option2</li></ul>")

    assert sel.getall(text=True) == ["option1\noption2"]
    assert sel.css("li").getall(text=True) == ["option1", "option2"]


def test_cleaned() -> None:
    div_html = "<div><script>SCRIPT</script>" "<style>STYLE</style><p>hello</p><div>"
    sel = Selector(div_html)
    assert sel.css("script").getall() == ["<script>SCRIPT</script>"]
    assert sel.cleaned().css("script").getall() == []

    assert len(sel.css("script")) == 1
    assert len(sel.css("style")) == 1
    assert len(sel.css("p")) == 1

    assert len(sel.cleaned().css("script")) == 0
    assert len(sel.cleaned().css("style")) == 1
    assert len(sel.cleaned().css("p")) == 1


def test_cleaned_options() -> None:
    div_html = "<div><script>SCRIPT</script>" "<style>STYLE</style><p>hello</p><div>"
    sel = Selector(div_html)
    assert len(sel.css("script")) == 1
    assert len(sel.css("style")) == 1
    assert len(sel.css("p")) == 1

    assert len(sel.cleaned().css("script")) == 0
    assert len(sel.cleaned().css("style")) == 1
    assert len(sel.cleaned().css("p")) == 1

    assert len(sel.cleaned("html").css("script")) == 0
    assert len(sel.cleaned("html").css("style")) == 1
    assert len(sel.cleaned("html").css("p")) == 1

    assert len(sel.cleaned("text").css("script")) == 0
    assert len(sel.cleaned("text").css("style")) == 0
    assert len(sel.cleaned("text").css("p")) == 1

    cleaner = Cleaner(kill_tags=["p"], scripts=False, style=False)
    assert len(sel.cleaned(cleaner).css("script")) == 1
    assert len(sel.cleaned(cleaner).css("style")) == 1
    assert len(sel.cleaned(cleaner).css("p")) == 0


def test_get_cleaner() -> None:
    div_html = "<div><script>SCRIPT</script><style>STYLE</style><p>P</p></div>"
    sel = Selector(div_html)
    cleaner = Cleaner(kill_tags=["p"], scripts=False, style=False)

    assert sel.get(text=True) == "P"
    assert sel.get(text=True, cleaner=None) == "SCRIPT STYLE\n\nP"
    assert sel.get(text=True, cleaner="html") == "STYLE\n\nP"
    assert sel.get(text=True, cleaner="text") == "P"
    assert sel.get(text=True, cleaner=cleaner) == "SCRIPT STYLE"

    div = sel.css("div")
    assert div.get() == div_html
    assert div.get(cleaner=None) == div_html
    assert div.get(cleaner="html") == "<div><style>STYLE</style><p>P</p></div>"
    assert div.get(cleaner="text") == "<div><p>P</p></div>"
    assert (
        div.get(cleaner=cleaner)
        == "<div><script>SCRIPT</script><style>STYLE</style></div>"
    )


def test_guess_punct_space() -> None:
    sel = Selector('<p>hello<b>"Folks"</b></p>')
    assert sel.get(text=True, guess_punct_space=False) == 'hello "Folks"'
    assert sel.get(text=True, guess_punct_space=True) == 'hello"Folks"'

    assert sel.getall(text=True, guess_punct_space=False) == ['hello "Folks"']
    assert sel.getall(text=True, guess_punct_space=True) == ['hello"Folks"']


def test_guess_layout() -> None:
    sel = Selector("<ul><li>option1</li><li>option2</li></ul>")
    assert sel.get(text=True, guess_layout=False) == "option1 option2"
    assert sel.get(text=True, guess_layout=True) == "option1\noption2"

    assert sel.getall(text=True, guess_layout=False) == ["option1 option2"]
    assert sel.getall(text=True, guess_layout=True) == ["option1\noption2"]
