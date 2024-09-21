// Function to open the modal and display component details
function openModal(name, domain, about, context, size, content) {
  document.getElementById("componentTitle").innerHTML = name;
  document.getElementById("componentDomain").innerHTML = domain;
  document.getElementById("componentAbout").innerHTML = about;
  document.getElementById("componentContext").innerHTML = context;
  document.getElementById("componentSize").innerHTML = size;
  document.getElementById("componentContent").innerHTML = content;

  // Open the modal
  var modal = document.getElementById("componentModal");
  modal.style.display = "block";
}

// Function to close the modal
function closeModal() {
  var modal = document.getElementById("componentModal");
  modal.style.display = "none";
}

// Function to copy content to clipboard
function copyToClipboard() {
  var content = document.getElementById("componentContent").innerHTML;
  var textarea = document.createElement("textarea");
  textarea.value = content;
  document.body.appendChild(textarea);
  textarea.select();
  document.execCommand("copy");
  document.body.removeChild(textarea);
}
