// Utility function to create tables from JSON data
function createTable(data, containerId) {
  if (data.length === 0) {
    document.getElementById(containerId).innerHTML = "<p>No data available</p>";
    return;
  }

  const headers = Object.keys(data[0]);
  let table = "<table><thead><tr>";

  // Create headers
  headers.forEach((header) => {
    table += `<th>${header.replace(/_/g, " ").toUpperCase()}</th>`;
  });
  table += "</tr></thead><tbody>";

  // Create rows
  data.forEach((row) => {
    table += "<tr>";
    headers.forEach((header) => {
      table += `<td>${row[header]}</td>`;
    });
    table += "</tr>";
  });

  table += "</tbody></table>";
  document.getElementById(containerId).innerHTML = table;
}

// Show message function
function showMessage(containerId, message, isError = false) {
  const messageDiv = document.getElementById(containerId);
  messageDiv.textContent = message;
  messageDiv.className = `message ${isError ? "error" : "success"}`;
  setTimeout(() => {
    messageDiv.className = "message";
  }, 10000);
}

// Load High Risk Pathogens
async function loadHighRiskPathogens() {
  const threshold = document.getElementById("mutationThreshold").value;
  try {
    const response = await fetch(
      `/api/high_risk_pathogens/${parseFloat(threshold)}`
    );
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    createTable(data, "highRiskPathogensTable");
  } catch (error) {
    console.error("Error:", error);
    document.getElementById("highRiskPathogensTable").innerHTML =
      '<p class="error">Error loading pathogen data. Please try again.</p>';
  }
}

async function loadPrimaryKeys(table, containerId, delrecord=false) {
  try {
    const response = await fetch(`/api/get_primary_keys/${table}`);
    const result = await response.json();

    if (result.status === "error") {
      showMessage(containerId, result.message, true);
      return;
    }

    const primaryKeys = result.primary_keys;
    const formContainer = document.getElementById(containerId);

    formContainer.innerHTML = "";
    primaryKeys.forEach((key) => {
      formContainer.innerHTML += `
        <div class="form-group">
          <label>${key.replace(/_/g, " ")}</label>
          <input type="text" id="${key}-field" name="${key}" required />
        </div>
      `;
    });

    const editablerec = (delrecord === true ? false : true)
    formContainer.innerHTML += `
      <button type="button" onclick="loadRecord('${table}', '${containerId}', ${editablerec ? "true" : "false"})">
        Load Record
      </button>
    `;
  } catch (error) {
    console.error("Error loading primary keys:", error);
  }
}

async function loadRecord(table, containerId, editable = true) {
  const formContainer = document.getElementById(containerId);
  const inputs = formContainer.querySelectorAll("input");
  const keys = {};

  inputs.forEach((input) => {
    keys[input.name] = input.value;
  });

  try {
    const response = await fetch(`/api/get/${table}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(keys),
    });

    const result = await response.json();

    if (result.status === "error") {
      showMessage(containerId, result.message, true);
      return;
    }

    const data = result.data;
    let formHTML = "<form>";
    for (const key in data) {
      formHTML += `
        <div class="form-group">
          <label>${key.replace(/_/g, " ")}</label>
          <input 
            type="text" 
            value="${data[key]}" 
            ${editable ? "" : "readonly"} 
            id="${key}-field"
            name="${key}"
          />
        </div>
      `;
    }

    formHTML += `
      <button type="button" onclick="${editable ? "updateRecord" : "deleteRecord"}('${table}', '${containerId}')">
        ${editable ? "Update Values" : "Delete"}
      </button>
    </form>`;
    formContainer.innerHTML = formHTML;
  } catch (error) {
    console.error("Error loading record:", error);
  }
}

async function deleteRecord(table, containerId) {
  const inputs = document.querySelectorAll(`#${containerId} input`);
  const keys = {};

  inputs.forEach((input) => {
    keys[input.name] = input.value;
  });

  try {
    const constraintResponse = await fetch(`/api/check_constraints/${table}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(keys),
    });

    const constraintResult = await constraintResponse.json();
    console.log(constraintResult);

    if (constraintResult.status === "warning") {
      // Handle RESTRICT constraints
      if (constraintResult.restrict_t) {
        alert(constraintResult.message + " Cannot delete."); // Show message for RESTRICT
        return; // Do not proceed with deletion
      }

      // Handle CASCADE constraints
      if (constraintResult.cascade_t) {
        if (!confirm(constraintResult.message + "Do you want to proceed with deletion?")) {
          return; // Do not delete if canceled
        }
        // else, proceed to delete (below)
      }
    
    } else if (constraintResult.status === "error") {
      showMessage(containerId, constraintResult.message, true);
      return;
    }
    
    // proceed to delete
    const deleteResponse = await fetch(`/api/delete/${table}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(keys),
    });

    const deleteResult = await deleteResponse.json();
    showMessage(containerId, deleteResult.message, deleteResult.status === "error");
  } catch (error) {
    console.error("Error deleting record:", error);
  }
}

async function updateRecord(table, containerId) {
  const inputs = document.querySelectorAll(`#${containerId} input`);
  const updatedData = {};

  inputs.forEach((input) => {
    updatedData[input.name] = input.value;
  });

  try {
    const response = await fetch(`/api/update/${table}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(updatedData),
    });

    const result = await response.json();
    console.log(result);
    showMessage(containerId, result.message, result.status === "error");
  } catch (error) {
    console.error("Error updating record:", error);
  }
}

// Load Research Labs
async function loadResearchLabs() {
  const pathogenType = document.getElementById("pathogenType").value;
  try {
    const response = await fetch(`/api/labs_by_pathogen_type/${pathogenType}`);
    const data = await response.json();
    createTable(data, "researchLabsTable");
  } catch (error) {
    console.error("Error:", error);
  }
}

// Load Vaccine Distribution Stats
async function loadVaccineStats() {
  try {
    const response = await fetch("/api/vaccine_distribution_stats");
    const data = await response.json();
    createTable(data, "vaccineDistributionTable");
  } catch (error) {
    console.error("Error:", error);
  }
}

// Load Mutation Impact
async function loadMutationImpact() {
  try {
    const response = await fetch("/api/mutation_impact");
    const data = await response.json();
    createTable(data, "mutationImpactTable");
  } catch (error) {
    console.error("Error:", error);
  }
}

// Load Project Success
async function loadProjectSuccess() {
  try {
    const response = await fetch("/api/project_success_metrics");
    const data = await response.json();
    createTable(data, "projectSuccessTable");
  } catch (error) {
    console.error("Error:", error);
  }
}

// Update Vaccine Effectiveness
async function updateVaccineEffectiveness() {
  const vaccineId = document.getElementById("vaccineId").value;
  const effectiveness = document.getElementById("vaccineEffectiveness").value;

  try {
    const response = await fetch("/api/update_vaccine_effectiveness", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        vaccine_id: vaccineId,
        effectiveness: effectiveness,
      }),
    });

    const result = await response.json();
    showMessage(
      "vaccineUpdateMessage",
      result.message,
      result.status === "error"
    );
  } catch (error) {
    showMessage(
      "vaccineUpdateMessage",
      "Failed to update vaccine effectiveness",
      true
    );
  }
}

// Update Project Status
async function updateProjectStatus() {
  const projectId = document.getElementById("projectId").value;
  const status = document.getElementById("projectStatus").value;

  try {
    const response = await fetch("/api/update_project_status", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        project_id: projectId,
        status: status,
        end_date:
          status === "completed"
            ? new Date().toISOString().split("T")[0]
            : null,
      }),
    });

    const result = await response.json();
    showMessage(
      "projectUpdateMessage",
      result.message,
      result.status === "error"
    );
  } catch (error) {
    showMessage(
      "projectUpdateMessage",
      "Failed to update project status",
      true
    );
  }
}

// Update Lab Funding
async function updateLabFunding() {
  const labId = document.getElementById("labId").value;
  const fundingChange = document.getElementById("fundingChange").value;

  try {
    const response = await fetch("/api/update_lab_funding", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        lab_id: labId,
        funding_change: fundingChange,
      }),
    });

    const result = await response.json();
    showMessage("labUpdateMessage", result.message, result.status === "error");
  } catch (error) {
    showMessage("labUpdateMessage", "Failed to update lab funding", true);
  }
}

// Add event listener when document loads
document.addEventListener("DOMContentLoaded", function () {
  const cards = document.querySelectorAll(".card");

  cards.forEach((card) => {
    card.addEventListener("click", function () {
      // Remove active class from all cards
      cards.forEach((c) => c.classList.remove("active"));
      // Add active class to clicked card
      this.classList.add("active");
    });
  });

  // Add input validation for mutation threshold
  const mutationThreshold = document.getElementById("mutationThreshold");
  if (mutationThreshold) {
    mutationThreshold.addEventListener("input", function () {
      let value = parseFloat(this.value);
      if (value < 0) this.value = 0;
      if (value > 100) this.value = 100;
    });
  }
});

// Table configurations
const tables = [
  "Country",
  "Country_response_to_pathogen",
  "Global_vaccine_distribution",
  "Government_response",
  "Infection",
  "Milestones",
  "Mutation",
  "Pathogen",
  "Project_under_lab",
  "Research_aim",
  "Research_focus",
  "Research_lab",
  "Research_project",
  "Resistance",
  "Vaccine",
  "Vaccine_development",
  "Vaccine_distribution_cost",
];

// Initialize the page
document.addEventListener("DOMContentLoaded", function () {
  // Populate table dropdowns
  const tableSelects = ["insert-table", "update-table", "delete-table"];
  tableSelects.forEach((selectId) => {
    const select = document.getElementById(selectId);
    tables.forEach((table) => {
      const option = document.createElement("option");
      option.value = table;
      option.textContent = table.replace(/_/g, " ");
      select.appendChild(option);
    });
  });

  // Populate table dropdowns for update and delete
  fetch("/api/tables")
    .then((response) => response.json())
    .then((tables) => {
      const updateTableSelect = document.getElementById("update-table");
      const deleteTableSelect = document.getElementById("delete-table");

      tables.forEach((table) => {
        const updateOption = document.createElement("option");
        updateOption.value = table;
        updateOption.textContent = table;
        updateTableSelect.appendChild(updateOption);

        const deleteOption = document.createElement("option");
        deleteOption.value = table;
        deleteOption.textContent = table;
        deleteTableSelect.appendChild(deleteOption);
      });
    });
});

// Modal functions
function openModal(modalId) {
  document.getElementById(modalId).style.display = "block";
}

function closeModal(modalId) {
  document.getElementById(modalId).style.display = "none";
  // Clear any forms or results
  const formContainer = document.getElementById(`${modalId}-form-container`);
  if (formContainer) formContainer.innerHTML = "";
  const resultsContainer = document.getElementById("analysis-results");
  if (resultsContainer) resultsContainer.innerHTML = "";
  
  const cards = document.querySelectorAll(".card");
  cards.forEach((c) => c.classList.remove("active"));
}

// Load table form based on operation type
async function loadTableForm(operation) {
  const table = document.getElementById(`${operation}-table`).value;
  if (!table) return;

  try {
    const response = await fetch(`/api/table-schema/${table}`);
    const schema = await response.json();

    const formContainer = document.getElementById(`${operation}-form-container`);
    formContainer.innerHTML = ""; // Clear the container

    let formHTML = `<form id="${operation}-form">`;

    // Create form rows for each field
    schema.forEach((field) => {
      formHTML += `
        <div class="form-group">
          <label>${field.name.replace(/_/g, " ")}</label>
          <input 
            type="${field.type === "number" ? "number" : "text"}" 
            id="${field.name}-field" 
            name="${field.name}" 
            ${field.required ? "required" : ""} 
            placeholder="Enter ${field.name.replace(/_/g, " ")}" />
        </div>
      `;
    });

    // Add a submit button
    formHTML += `
      <button type="submit">
        ${operation.charAt(0).toUpperCase() + operation.slice(1)}
      </button>
    `;
    formHTML += "</form>";

    formContainer.innerHTML = formHTML;

    // Attach event handler to the form
    const form = document.getElementById(`${operation}-form`);
    form.addEventListener("submit", (e) => handleFormSubmit(e, operation, table));
  } catch (error) {
    console.error("Error loading table schema:", error);
  }
}

// Create form field based on schema
function createFormField(field, operation) {
  const div = document.createElement("div");
  div.className = "form-row";

  const label = document.createElement("label");
  label.textContent = field.name.replace(/_/g, " ");
  label.htmlFor = `${field.name}-input`;

  const input = document.createElement("input");
  input.id = `${field.name}-input`;
  input.name = field.name;
  input.required = field.required;

  // Set input type based on field type
  switch (field.type) {
    case "number":
      input.type = "number";
      if (field.min !== undefined) input.min = field.min;
      if (field.max !== undefined) input.max = field.max;
      break;
    case "date":
      input.type = "date";
      break;
    default:
      input.type = "text";
  }

  div.appendChild(label);
  div.appendChild(input);
  return div;
}

// Handle form submission
async function handleFormSubmit(event, operation, table) {
  event.preventDefault();
  const formData = new FormData(event.target);
  const data = Object.fromEntries(formData.entries());

  try {
    const response = await fetch(`/api/${operation}/${table}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    });

    const result = await response.json();
    showMessage(result.message, result.status === "error");
  } catch (error) {
    showMessage("An error occurred while processing your request.", true);
  }
}

// Load analysis results
// Load analysis results
async function loadAnalysis(type) {
  const resultsContainer = document.getElementById("analysis-results");
  resultsContainer.innerHTML = "<p>Loading...</p>";

  try {
    const response = await fetch(`/api/analysis/${type}`);
    const data = await response.json();

    // Create table from data
    if (Array.isArray(data)) {
      createTable(data, "analysis-results");
    } else {
      let table = "<table><thead><tr>";
      const headers = Object.keys(data);
      headers.forEach((header) => {
        table += `<th>${header.replace(/_/g, " ").toUpperCase()}</th>`;
      });
      table += "</tr></thead><tbody><tr>";
      headers.forEach((header) => {
        table += `<td>${data[header]}</td>`;
      });
      table += "</tr></tbody></table>";
      resultsContainer.innerHTML = table;
    }
  } catch (error) {
    resultsContainer.innerHTML =
      '<p class="error-message">Error loading analysis results.</p>';
  }
}

// Utility function to create tables from JSON data
// function createTable(data, containerId) {
//   if (data.length === 0) {
//     document.getElementById(containerId).innerHTML = "<p>No data available</p>";
//     return;
//   }

//   const headers = Object.keys(data[0]);
//   let table = "<table><thead><tr>";

//   // Create headers
//   headers.forEach((header) => {
//     table += <th>${header.replace(/_/g, " ").toUpperCase()}</th>;
//   });
//   table += "</tr></thead><tbody>";

//   // Create rows
//   data.forEach((row) => {
//     table += "<tr>";
//     headers.forEach((header) => {
//       table += <td>${row[header]}</td>;
//     });
//     table += "</tr>";
//   });

//   table += "</tbody></table>";
//   document.getElementById(containerId).innerHTML = table;
// }

// Show message function
function showMessage(message, isError = false) {
  const messageDiv = document.createElement("div");
  messageDiv.className = isError ? "error-message" : "success-message";
  messageDiv.textContent = message;

  const container = document.querySelector(".modal-content");
  container.appendChild(messageDiv);

  setTimeout(() => {
    messageDiv.remove();
  }, 3000);
}

// Close modal when clicking outside
window.onclick = function (event) {
  if (event.target.classList.contains("modal")) {
    event.target.style.display = "none";
  }
};

async function fetchTableData(table) {
  try {
    const response = await fetch(`/api/read/${table}`);
    const data = await response.json();
    createTable(data, "readTableContainer");
  } catch (error) {
    console.error("Error fetching table data:", error);
  }
}

function loadTableSchema(table, containerId, forUpdate = false) {
  fetch(`/api/table-schema/${table}`)
    .then((res) => res.json())
    .then((schema) => {
      const container = document.getElementById(containerId);
      container.innerHTML = "";

      schema.forEach((field) => {
        const row = document.createElement("div");
        row.className = "form-row";

        const label = document.createElement("label");
        label.textContent = field.name.replace(/_/g, " ");
        row.appendChild(label);

        if (forUpdate) {
          const input = document.createElement("input");
          input.name = field.name;
          input.placeholder = "Enter value or leave blank";
          row.appendChild(input);
        } else {
          const btn = document.createElement("button");
          btn.textContent = `Delete ${field.name}`;
          btn.onclick = () => deleteRow(table, field.name);
          row.appendChild(btn);
        }
        container.appendChild(row);
      });
    })
    .catch((err) => console.error(err));
}

async function fetchTableData(table) {
  if (!table) return;

  try {
    const response = await fetch(`/api/read/${table}`);
    const data = await response.json();

    const tableContainer = document.getElementById("readTableContainer");
    tableContainer.innerHTML = "";

    if (data.status === "error") {
      tableContainer.innerHTML = `<p>Error: ${data.message}</p>`;
      return;
    }

    const tableElement = document.createElement("table");
    const thead = document.createElement("thead");
    const tbody = document.createElement("tbody");

    // Create table headers
    const headers = Object.keys(data[0]);
    const headerRow = document.createElement("tr");
    headers.forEach((header) => {
      const th = document.createElement("th");
      th.textContent = header;
      headerRow.appendChild(th);
    });
    thead.appendChild(headerRow);

    // Create table rows
    data.forEach((row) => {
      const tr = document.createElement("tr");
      headers.forEach((header) => {
        const td = document.createElement("td");
        td.textContent = row[header];
        tr.appendChild(td);
      });
      tbody.appendChild(tr);
    });

    tableElement.appendChild(thead);
    tableElement.appendChild(tbody);
    tableContainer.appendChild(tableElement);
  } catch (error) {
    console.error("Error fetching table data:", error);
  }
}

async function loadTableOptions() {
  try {
    const response = await fetch("/api/tables");
    const tables = await response.json();

    const select = document.getElementById("read-table");
    tables.forEach((table) => {
      const option = document.createElement("option");
      option.value = table;
      option.textContent = table;
      select.appendChild(option);
    });
  } catch (error) {
    console.error("Error loading table options:", error);
  }
}

document.addEventListener("DOMContentLoaded", loadTableOptions);

document.addEventListener("DOMContentLoaded", function () {
  const selectionTableSelect = document.getElementById("selection-table");
  const projectionTableSelect = document.getElementById("projection-table");
  const aggregationTableSelect = document.getElementById("aggregation-table");
  const searchTableSelect = document.getElementById("search-table");

  fetch("/api/tables")
    .then((response) => response.json())
    .then((tables) => {
      const selectElements = [
        selectionTableSelect,
        projectionTableSelect,
        aggregationTableSelect,
        searchTableSelect,
      ];

      selectElements.forEach((select) => {
        tables.forEach((table) => {
          const option = document.createElement("option");
          option.value = table;
          option.textContent = table;
          select.appendChild(option);
        });
      });
    });
});

function loadSelectionOptions(table) {
  fetch(`/api/tables/columns?table=${table}`)
    .then((response) => response.json())
    .then((columns) => {
      const columnSelect = document.getElementById("selection-column");
      columnSelect.innerHTML = "";
      columns.forEach((column) => {
        const option = document.createElement("option");
        option.value = column;
        option.textContent = column;
        columnSelect.appendChild(option);
      });
    });
}

function performSelection() {
  const table = document.getElementById("selection-table").value;
  const column = document.getElementById("selection-column").value;
  const condition = document.getElementById("selection-condition").value;
  const value = document.getElementById("selection-value").value;

  fetch("/api/selection", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ table, column, condition, value }),
  })
    .then((response) => response.json())
    .then((data) => {
      const resultsContainer = document.getElementById("selection-results");
      createTable(data, "selection-results");
    })
    .catch((error) => {
      console.error("Error:", error);
      const resultsContainer = document.getElementById("selection-results");
      resultsContainer.innerHTML =
        '<p class="error">Error performing selection</p>';
    });
}

function performProjection() {
  const table = document.getElementById("projection-table").value;
  const columnCheckboxes = document.querySelectorAll(
    'input[name="projection-columns"]:checked'
  );
  const columns = Array.from(columnCheckboxes).map((cb) => cb.value);

  fetch("/api/projection", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ table, columns }),
  })
    .then((response) => response.json())
    .then((data) => createTable(data, "projection-results"))
    .catch((error) => {
      console.error("Error:", error);
    });
}

function performAggregation() {
  const table = document.getElementById("aggregation-table").value;
  const column = document.getElementById("aggregation-column").value;
  const operation = document.getElementById("aggregation-operation").value;

  fetch("/api/aggregation", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ table, column, operation }),
  })
    .then((response) => response.json())
    .then((data) => createTable(data, "aggregation-results"))
    .catch((error) => {
      console.error("Error:", error);
    });
}

function performSearch() {
  const table = document.getElementById("search-table").value;
  const column = document.getElementById("search-column").value;
  const pattern = document.getElementById("search-pattern").value;

  fetch("/api/search", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ table, column, pattern }),
  })
    .then((response) => response.json())
    .then((data) => createTable(data, "search-results"))
    .catch((error) => {
      console.error("Error:", error);
    });
}

function loadProjectionColumns(table) {
  fetch(`/api/tables/columns?table=${table}`)
    .then((response) => response.json())
    .then((columns) => {
      const columnsContainer = document.getElementById("projection-columns");
      columnsContainer.innerHTML = "";
      columns.forEach((column) => {
        const div = document.createElement("div");
        div.innerHTML = `
                  <input type="checkbox" name="projection-columns" 
                         id="projection-${column}" value="${column}">
                  <label for="projection-${column}">${column}</label>
              `;
        columnsContainer.appendChild(div);
      });
    });
}

function loadAggregationColumns(table) {
  fetch(`/api/tables/columns?table=${table}`)
    .then((response) => response.json())
    .then((columns) => {
      const columnSelect = document.getElementById("aggregation-column");
      columnSelect.innerHTML = "";
      columns.forEach((column) => {
        const option = document.createElement("option");
        option.value = column;
        option.textContent = column;
        columnSelect.appendChild(option);
      });
    });
}

function loadSearchColumns(table) {
  fetch(`/api/tables/columns?table=${table}`)
    .then((response) => response.json())
    .then((columns) => {
      const columnSelect = document.getElementById("search-column");
      columnSelect.innerHTML = "";
      columns.forEach((column) => {
        const option = document.createElement("option");
        option.value = column;
        option.textContent = column;
        columnSelect.appendChild(option);
      });
    });
}

// Add these to the existing script.js file

// Drag and drop functionality for tiles
document.addEventListener("DOMContentLoaded", function () {
  const grid = document.querySelector(".grid");

  // Make tiles draggable
  const tiles = document.querySelectorAll(".card.operation-card");
  tiles.forEach((tile) => {
    tile.setAttribute("draggable", "true");

    tile.addEventListener("dragstart", dragStart);
    tile.addEventListener("dragend", dragEnd);
    tile.addEventListener("dragover", dragOver);
    tile.addEventListener("dragenter", dragEnter);
    tile.addEventListener("dragleave", dragLeave);
    tile.addEventListener("drop", drop);
  });

  function dragStart(e) {
    this.classList.add("dragging");
    e.dataTransfer.setData("text/plain", this.id);
  }

  function dragEnd(e) {
    this.classList.remove("dragging");
  }

  function dragOver(e) {
    e.preventDefault();
  }

  function dragEnter(e) {
    e.preventDefault();
    this.classList.add("drag-over");
  }

  function dragLeave() {
    this.classList.remove("drag-over");
  }

  function drop(e) {
    e.preventDefault();
    this.classList.remove("drag-over");

    const draggedTileId = e.dataTransfer.getData("text/plain");
    const draggedTile = document.getElementById(draggedTileId);

    // Swap tiles
    const currentTile = e.currentTarget;
    const tempHTML = currentTile.innerHTML;
    const tempId = currentTile.id;
    const tempOnclick = currentTile.getAttribute("onclick");

    currentTile.innerHTML = draggedTile.innerHTML;
    currentTile.id = draggedTile.id;
    currentTile.setAttribute("onclick", draggedTile.getAttribute("onclick"));

    draggedTile.innerHTML = tempHTML;
    draggedTile.id = tempId;
    draggedTile.setAttribute("onclick", tempOnclick);

    // Save layout to localStorage
    saveTileLayout();
  }

  // Persist tile layout
  function saveTileLayout() {
    const tiles = Array.from(
      document.querySelectorAll(".card.operation-card")
    ).map((tile) => ({
      id: tile.id,
      innerHTML: tile.innerHTML,
      onclick: tile.getAttribute("onclick"),
    }));
    localStorage.setItem("tileLayout", JSON.stringify(tiles));
  }

  // Restore tile layout from localStorage
  function restoreTileLayout() {
    const savedLayout = localStorage.getItem("tileLayout");
    if (savedLayout) {
      const tiles = JSON.parse(savedLayout);
      const currentTiles = document.querySelectorAll(".card.operation-card");

      tiles.forEach((savedTile, index) => {
        if (currentTiles[index]) {
          currentTiles[index].id = savedTile.id;
          currentTiles[index].innerHTML = savedTile.innerHTML;
          currentTiles[index].setAttribute("onclick", savedTile.onclick);
        }
      });
    }
  }

  // Add unique IDs to tiles if not already present
  tiles.forEach((tile, index) => {
    if (!tile.id) {
      tile.id = `tile-${index + 1}`;
    }
  });

  // Restore layout on page load
  restoreTileLayout();
});