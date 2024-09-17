function showContent(content) {
  const popup = window.open("", "Component Content", "width=600,height=400");
  popup.document.write("<pre>" + content + "</pre>");
  popup.document.write('<button onclick="window.close()">Close</button>');
}

// JavaScript function for copying content to clipboard
function copyToClipboard() {
  const content = document.querySelector("pre").innerText; // Get the content from the <pre> tag
  navigator.clipboard.writeText(content).then(
    function () {
      alert("Content copied to clipboard");
    },
    function (err) {
      alert("Failed to copy content: ", err);
    }
  );
}
