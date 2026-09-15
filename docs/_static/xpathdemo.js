// Interactive XPath playground for the parsel documentation.
//
// Each ``.xpath-demo`` panel (rendered by the ``xpathdemo`` Sphinx directive)
// holds an HTML input, an XPath expression and a result area. Expressions are
// evaluated in the browser with the native ``document.evaluate()`` XPath 1.0
// engine, which behaves closely to the libxml2 engine used by parsel/lxml.

(function () {
  "use strict";

  function serializeNode(node) {
    switch (node.nodeType) {
      case Node.ATTRIBUTE_NODE:
        return node.name + '="' + node.value + '"';
      case Node.TEXT_NODE:
      case Node.CDATA_SECTION_NODE:
        return node.data;
      case Node.COMMENT_NODE:
        return "<!--" + node.data + "-->";
      case Node.PROCESSING_INSTRUCTION_NODE:
        return "<?" + node.target + " " + node.data + "?>";
      case Node.DOCUMENT_NODE:
        return new XMLSerializer().serializeToString(node.documentElement);
      default:
        return new XMLSerializer().serializeToString(node);
    }
  }

  function appendResultNode(output, text) {
    var div = document.createElement("div");
    div.className = "xpath-demo-result";
    div.textContent = text;
    output.appendChild(div);
  }

  function appendScalar(output, kind, text) {
    var div = document.createElement("div");
    div.className = "xpath-demo-result xpath-demo-scalar";
    div.textContent = text;
    div.setAttribute("data-kind", kind);
    output.appendChild(div);
  }

  function appendPlaceholder(output, text) {
    var div = document.createElement("div");
    div.className = "xpath-demo-empty";
    div.textContent = text;
    output.appendChild(div);
  }

  function parseInput(htmlText) {
    var doc = new DOMParser().parseFromString(htmlText, "application/xml");
    var error = doc.querySelector("parsererror");
    if (error) {
      throw new Error("could not parse the HTML input as XML: " + error.textContent.trim());
    }
    return doc;
  }

  function render(output, expression, htmlText) {
    output.textContent = "";
    output.classList.remove("xpath-demo-output--error");

    if (!expression.trim()) {
      return;
    }

    var result;
    try {
      var doc = parseInput(htmlText);
      result = doc.evaluate(expression, doc, null, XPathResult.ANY_TYPE, null);
    } catch (err) {
      output.classList.add("xpath-demo-output--error");
      appendResultNode(output, "Error: " + err.message);
      return;
    }

    switch (result.resultType) {
      case XPathResult.NUMBER_TYPE:
        appendScalar(output, "number", String(result.numberValue));
        return;
      case XPathResult.STRING_TYPE:
        appendScalar(output, "string", JSON.stringify(result.stringValue));
        return;
      case XPathResult.BOOLEAN_TYPE:
        appendScalar(output, "boolean", String(result.booleanValue));
        return;
      default:
        break;
    }

    var count = 0;
    var node;
    while ((node = result.iterateNext()) !== null) {
      appendResultNode(output, serializeNode(node));
      count += 1;
    }
    if (count === 0) {
      appendPlaceholder(output, "No nodes matched.");
    }
  }

  function setupPanel(panel) {
    var input = panel.querySelector(".xpath-demo-input");
    var expression = panel.querySelector(".xpath-demo-expression");
    var output = panel.querySelector(".xpath-demo-output");
    if (!input || !expression || !output) {
      return;
    }

    function update() {
      render(output, expression.value, input.value);
    }

    expression.addEventListener("input", update);
    input.addEventListener("input", update);
    update();
  }

  document.addEventListener("DOMContentLoaded", function () {
    var panels = document.querySelectorAll(".xpath-demo");
    Array.prototype.forEach.call(panels, setupPanel);
  });
})();
