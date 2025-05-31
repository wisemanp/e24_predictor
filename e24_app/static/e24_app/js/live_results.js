function saveData() {
  const fixedLaps = parseInt(document.getElementById("fixedLapCount")?.textContent) || 0;

  const data = {
    predictions: Array.from(document.querySelectorAll("#teamPredictions tbody tr")).map(row => {
      const dropdown = row.querySelector(".runner-dropdown");
      const minutes = row.querySelector(".runner-minutes")?.value || 0;
      const seconds = row.querySelector(".runner-seconds")?.value || 0;
      return {
        runner: dropdown?.value || "",
        minutes: parseInt(minutes),
        seconds: parseInt(seconds),
      };
    }),

    race: Array.from(document.querySelectorAll("#raceTable tbody tr")).map((row, index) => {
      const runnerField = row.querySelector(".runner-field");
      const laptimeField = row.querySelector(".laptime");
      const checkbox = row.querySelector(".lap-complete");

      if (!runnerField || !laptimeField) return null;

      return {
        number: fixedLaps + index + 1,  // Offset lap number
        runner: runnerField.value,
        laptime: laptimeField.value,
        complete: checkbox?.checked || false,
        fixed_prediction: row.hasAttribute("data-fixed-prediction") // Add fixed_prediction attribute
      };
    }).filter(row => row !== null)
  };

  fetch('/save-predictions/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value,
    },
    body: JSON.stringify(data),
  })
  .then(response => response.json())
  .then(data => console.log('Save response:', data))
  .catch(error => console.error('Error saving data:', error));

  localStorage.setItem("raceData", JSON.stringify(data));
}

function loadData() {
  const saved = localStorage.getItem("raceData");
  if (!saved) return;
  const data = JSON.parse(saved);

  // Restore team predictions
  const predictionRows = document.querySelectorAll("#teamPredictions tbody tr");
  predictionRows.forEach((row, i) => {
    const dropdown = row.querySelector(".runner-dropdown");
    const minutesInput = row.querySelector(".runner-minutes");
    const secondsInput = row.querySelector(".runner-seconds");

    const savedPrediction = data.predictions[i];
    if (savedPrediction) {
      if (dropdown) dropdown.value = savedPrediction.runner;
      if (minutesInput) minutesInput.value = savedPrediction.minutes;
      if (secondsInput) secondsInput.value = savedPrediction.seconds;

      updatePace(minutesInput); // recalculate pace cell
    }
  });

  // Restore predicted race rows (non-fixed only)
  const raceRows = document.querySelectorAll("#raceTable tbody tr");
  data.race.forEach((lap, i) => {
    const row = raceRows[i];
    if (!row) return;

    const runnerField = row.querySelector(".runner-field");
    const laptimeField = row.querySelector(".laptime");
    const checkbox = row.querySelector(".lap-complete");

    if (runnerField) runnerField.value = lap.runner;
    if (laptimeField) laptimeField.value = lap.laptime;
    if (checkbox && !checkbox.disabled) {
    checkbox.checked = lap.complete;
}


    // ✅ Only set data-fixed-prediction on editable rows
    if (lap.fixed_prediction && runnerField) {
      row.setAttribute("data-fixed-prediction", "true");
      const fixBox = row.querySelector(".fix-row");
      if (fixBox) fixBox.checked = true;
    }

    // ✅ Only apply .completed class to editable rows
    if (checkbox && !checkbox.disabled) {
      row.classList.toggle("completed", checkbox.checked);
    }
  });

  updateTimes(); // refresh Start Time, Pace, Total Time
}


function generateLapRows() {
  const lapCount = parseInt(document.getElementById("lapCount").value) || 0;
  const raceTableBody = document.querySelector("#raceTable tbody");
  const currentRowCount = raceTableBody.querySelectorAll("tr").length;

  // Get the cumulative time after fixed laps from the hidden element
  const cumulativeTimeStr = document.getElementById("cumulativeTime").textContent;
  let cumulativeSeconds = parseTime(cumulativeTimeStr); // Use cumulativeTime from the backend

  const baseTime = new Date();
  baseTime.setHours(12, 0, 0, 0); // Base start time: 12:00:00

  // Add rows if the new lap count is greater than the current row count
  for (let i = currentRowCount + 1; i <= lapCount; i++) {
    const row = document.createElement("tr");
    const startTime = new Date(baseTime.getTime() + cumulativeSeconds * 1000);

    row.innerHTML = `
      <td>${i}</td>
      <td class="start-time">${startTime.toTimeString().substring(0, 8)}</td>
      <td><input type="text" class="runner-field" placeholder="Runner"></td>
      <td><input type="text" class="laptime" placeholder="HH:MM:SS" oninput="updateTimes(); saveData();"></td>
      <td class="pace-cell">-</td>
      <td class="total-time"></td>
      <td><input type="checkbox" class="lap-complete" onchange="toggleRowCompletion(this); saveData();"></td>
    `;
    raceTableBody.appendChild(row);

    // Update cumulative time (default lap time is 0 if not set)
    cumulativeSeconds += 0;
  }

  // Remove rows if the new lap count is less than the current row count
  while (raceTableBody.querySelectorAll("tr").length > lapCount) {
    raceTableBody.removeChild(raceTableBody.lastChild);
  }

  setTimeout(updateTimes, 0);
}
function confirmPopulate() {
  console.log("Confirm Populate triggered");
  if (confirm("Are you sure you want to populate predictions?")) {
    populateRunners();
    saveData(); // Ensure saveData is defined elsewhere
  }
}

function populateRunners() {
  const dropdowns = document.querySelectorAll(".runner-dropdown");
  const minuteInputs = document.querySelectorAll(".runner-minutes");
  const secondInputs = document.querySelectorAll(".runner-seconds");
  const dfactorInputs = document.querySelectorAll(".runner-dfactor");

  // Collect predictions from the Team Predictions table
  const runners = Array.from(dropdowns).map((dropdown, index) => {
    return {
      name: dropdown.value.trim(),
      minutes: parseInt(minuteInputs[index].value) || 0,
      seconds: parseInt(secondInputs[index].value) || 0,
      dfactor: parseFloat(dfactorInputs[index].value) || 1, // Default D Factor is 1
      laps: 0 // Track the number of laps for each runner
    };
  }).filter(runner => runner.name); // Filter out empty rows

  console.log("Collected Runners:", runners);

  const raceTableBody = document.querySelector("#raceTable tbody");
  const rows = raceTableBody.querySelectorAll("tr");

  let cumulativeSeconds = parseTime(document.getElementById("cumulativeTime").textContent); // Use cumulativeTime from the backend

  const baseTime = new Date();
  baseTime.setHours(12, 0, 0, 0); // Base start time: 12:00:00

  // Determine the starting index for predictions
  let startIndex = 0;

  // Check for the last fixed-prediction row
  const lastFixedRow = Array.from(rows).reverse().find(row => row.hasAttribute("data-fixed-prediction"));
  if (lastFixedRow) {
    const lastRunnerName = lastFixedRow.querySelector(".runner-field")?.value.trim();
    startIndex = runners.findIndex(runner => runner.name === lastRunnerName) + 1;
    if (startIndex >= runners.length) {
      startIndex = 0; // Wrap around to the beginning
    }
  } else {
    // Fallback to the most recent completed runner if no fixed predictions exist
    const lastCompletedRow = Array.from(rows).reverse().find(row => row.querySelector(".lap-complete")?.checked);
    if (lastCompletedRow) {
      const lastRunnerName = lastCompletedRow.querySelector(".runner-field")?.value.trim();
      startIndex = runners.findIndex(runner => runner.name === lastRunnerName) + 1;
      if (startIndex >= runners.length) {
        startIndex = 0; // Wrap around to the beginning
      }
    }
  }

  console.log(`Starting predictions from index: ${startIndex}`);

  let runnerIndex = startIndex; // Start predictions after the last fixed-prediction or completed runner

  rows.forEach((row, index) => {
    const runnerField = row.querySelector(".runner-field");
    const laptimeField = row.querySelector(".laptime");
    const startTimeCell = row.querySelector(".start-time");
    const totalTimeCell = row.querySelector(".total-time");
    const paceCell = row.querySelector(".pace-cell");
    const checkbox = row.querySelector(".lap-complete");

    if (!checkbox.checked && runnerField && !row.hasAttribute("data-fixed-prediction")) {
      // Only populate rows that are not marked as completed and are not fixed predictions
      const runner = runners[runnerIndex % runners.length];
      if (runner) {
        runnerField.value = runner.name;

        // Calculate lap time
        let lapSeconds = runner.minutes * 60 + runner.seconds;
        if (runner.laps > 0) { // Apply D Factor only for laps after the first
          lapSeconds = Math.round(lapSeconds * runner.dfactor);
        }

        const hh = String(Math.floor(lapSeconds / 3600)).padStart(2, '0');
        const mm = String(Math.floor((lapSeconds % 3600) / 60)).padStart(2, '0');
        const ss = String(lapSeconds % 60).padStart(2, '0');
        laptimeField.value = `${hh}:${mm}:${ss}`;

        // Update cumulative time
        const startTime = new Date(baseTime.getTime() + cumulativeSeconds * 1000);
        startTimeCell.textContent = startTime.toTimeString().substring(0, 8);

        cumulativeSeconds += lapSeconds;
        totalTimeCell.textContent = formatTime(cumulativeSeconds);

        // Calculate pace
        if (lapSeconds > 0) {
          const pacePerKm = lapSeconds / 8; // Assuming 8 km per lap
          const paceMinutes = String(Math.floor(pacePerKm / 60)).padStart(2, "0");
          const paceSeconds = String(Math.round(pacePerKm % 60)).padStart(2, "0");
          paceCell.textContent = `${paceMinutes}:${paceSeconds}/km`;
        } else {
          paceCell.textContent = "-";
        }

        // Update runner's predicted time for the next lap
        runner.minutes = Math.floor(lapSeconds / 60);
        runner.seconds = lapSeconds % 60;

        runner.laps++; // Increment the lap count for the runner
        runnerIndex++;
      }
    }
  });

  updateTimes(); // Recalculate times for all rows
}

function highlightNextLapRow() {
  const rows = document.querySelectorAll("#raceTable tbody tr");
  let currentLapFound = false;

  rows.forEach((row) => {
    const checkbox = row.querySelector(".lap-complete");

    // Preserve the "completed" class while removing "next-lap"
    if (!row.classList.contains("completed")) {
      row.classList.remove("next-lap");
    }

    if (row.classList.contains("highlight-current")) {
      currentLapFound = true; // Mark the current lap as found
    } else if (currentLapFound && !checkbox.checked) {
      row.classList.add("next-lap"); // Apply the "next-lap" class to the next lap
      currentLapFound = false; // Stop after marking the next lap
    }
  });
}

// Call the function periodically to update the next lap
setInterval(highlightNextLapRow, 1000);

function applyFixUpToRow(checkbox) {
  const row = checkbox.closest("tr");
  const rows = Array.from(document.querySelectorAll("#raceTable tbody tr"));
  const index = rows.indexOf(row);

  rows.forEach((r, i) => {
    if (i <= index) {
      r.setAttribute("data-fixed-prediction", "true");
      const fixBox = r.querySelector(".fix-row");
      if (fixBox) fixBox.checked = true;
    } else {
      r.removeAttribute("data-fixed-prediction");
      const fixBox = r.querySelector(".fix-row");
      if (fixBox) fixBox.checked = false;
    }
  });

  saveData();
}
