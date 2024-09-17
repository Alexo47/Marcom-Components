function showContent(content) {
  const popup = window.open("", "Component Content", "width=600,height=400");
  popup.document.write("<pre>" + content + "</pre>");
  popup.document.write('<button onclick="window.close()">Close</button>');
}
