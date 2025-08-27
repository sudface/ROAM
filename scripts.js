let SELECTED_DATE;
const lineColours = {
  "T1 North Shore": "#f89c1c", "T1 Western": "#f89c1c", "T2": "#0097cd", "T3": "#f35e21", "T4": "#015aa5", 
  "T5": "#c32190", "T6": "#4f6dab", "T7": "#6e818e", "T8": "#00964c", "T9": "#d21f2f", 
  "BMT": "#f89c1c", "SCO": "#015aa5", "SHL": "#00964c", "CCN": "#d21f2f", "HUN": "#833033", "M": "#168388", 
  "L1": "#BE1622", "L2": "#DD1E25", "L3": "#781140", "L4": "#BE1622", "NLR": "#EE343F",
  "F1": "#00774B", "F2": "#144734", "F3": "#648C3C", "F4": "#BFD730", "F5": "#286142", "F6": "#00AB51", 
  "F7": "#00B189", "F8": "#55622B", "F9": "#65B32E", "F10": "#5AB031" , "Stockton Ferry": "#5AB031", "MFF": "#3a78b6"
};

const doubleCapacityLines = ["M1", "L2", "L3"]

function parseYYYYMMDD(yyyymmdd) {
  const [y, m, d] = [yyyymmdd.slice(0, 4), yyyymmdd.slice(4, 6), yyyymmdd.slice(6, 8)];
  return new Date(parseInt(y), parseInt(m) - 1, parseInt(d));
}

// 08:23:34 => date obj
function parseTimeToDate(timeStr, date = new Date()) {
  const [h, m, s] = timeStr.split(':').map(Number);
  const d = new Date(date);
  d.setHours(h, m, s, 0);
  return d;
}

// Format YYYYMMDD -> "DD MMM YYYY"
function formatDate(yyyymmdd) {
  const [y, m, d] = [yyyymmdd.slice(0, 4), yyyymmdd.slice(4, 6), yyyymmdd.slice(6, 8)];
  const date = new Date(parseInt(y), parseInt(m) - 1, parseInt(d));
  return [date, `${date.toLocaleString('en-US', { weekday: 'short' })} ${d} ${date.toLocaleString('en-US', { month: 'short' })} ${y}`];
}

const OAMs = {
  "ROAM": ["Trains", "#F37021"],
  "FOAM": ["Ferries", "#00774B"],
  "LOAM": ["Light Rail", "#BE1622"],
  "BOAM": ["Buses", "#009ed7"],
};

function initDatatables() {
  // Create datatables with searchPane enabled
  $('#tripsTable').DataTable({
    dom: 'Plfrtip',
    searchPanes: {
      columns: [1, 2, 3, 4],
      dtOpts: {
        scrollY: '100px'
      },
      collapse: false,
    },
    order: [[5, 'asc']],
    columnDefs: [{ 
      targets: 6, 
      type: 'num-fmt',
      render: function ( data, type, row, meta ) {
        if ( type === 'display' && data === "0" ) {
          return "0-20";
        }
        return data;
      }
    },{
      targets: 2,
      render: function ( data, type, row, meta ) {
        if ( type === 'display') {
          if (["Up", "Inbound"].includes(data)) return "Towards City";
          if (["Down", "Outbound"].includes(data)) return "Away from City";
          return data;
        }
        return data;
      }
    }]
  });
}

function setMainColour(color) {
  function darkenColor(hex) {
    hex = hex.replace(/^#/, '');
    return '#' + [0,2,4].map(i => 
      Math.floor(parseInt(hex.slice(i,i+2),16) * 0.8)
          .toString(16).padStart(2,'0')
    ).join('');
  }

  document.documentElement.style.setProperty('--main-color', color);
  document.documentElement.style.setProperty('--dark-color', darkenColor(color));
}

function loadColour(load, capacity) {
  const ratio = load / capacity;
  if (ratio == 0) return "grey";
  if (ratio <= 0.25) return "green";
  if (ratio <= 0.5) return "darkorange";
  if (ratio <= 0.75) return "red";
  return "maroon";
}

function averageReducer(data, labels, step = 3) {
  const result = [];
  const resultLabels = [];
  step = Math.ceil(step);

  for (let i = 0; i < data.length; i += step) {
    const window = data.slice(i, i + step);
    const avg = window.reduce((a, b) => a + b, 0) / window.length;
    // divide by window length instead of step to account for the final window being small.
    
    result.push(avg);
    resultLabels.push(labels[i])
  }

  if (data.length % step !== 1) {
    result.push(data[data.length - 1]);
    resultLabels.push(labels[labels.length - 1]);
  }

  return [result, resultLabels];
}

function loadDirectory(nextSelectId, modeSelectPreFn, defaultLogic) {
  // Fetch directory.json and populate mode and date selects
  fetch('./processed/directory.json')
  .then(res => res.json())
  .then(data => {
    const modeSelect = document.getElementById('modeSelect');
    const dateSelect = document.getElementById('dateSelect');

    // Flatten files with path and group by mode
    // This method was so new that my vscode JS engine didn't even know about it
    // https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Object/groupBy
    const groupedFiles = Object.groupBy(
      Object.entries(data)
        .flatMap(([dir, files]) => files.map(file => dir + file))
        .map(path => {
          const match = path.match(/([LRFB]OAM)_(\d{8})\.json/);
          if (!match) return null;
          const [_, type, dateStr] = match;
          return {path, type, dateStr, date: formatDate(dateStr)[0]};
        })
        .filter(Boolean),
        ({type}) => type // This is some wild syntax
    )

    // Populate mode dropdown
    Object.keys(groupedFiles).forEach(type => {
      const option = document.createElement('option');
      option.value = type;
      option.textContent = OAMs[type][0];
      option.style.color = OAMs[type][1];
      modeSelect.appendChild(option);
    });

    
    // Handle mode selection
    modeSelect.addEventListener('change', () => {
      const selectedMode = modeSelect.value;
      modeSelectPreFn(selectedMode);
      dateSelect.innerHTML = '<option value="">Select a date...</option>';
      dateSelect.style.display = 'inline';

      groupedFiles[selectedMode]
        .sort((a, b) => b.date - a.date)
        .forEach(({path, dateStr}) => {
          const option = document.createElement('option');
          option.value = path;
          option.textContent = formatDate(dateStr)[1];
          dateSelect.appendChild(option);
        });

      // Hide all data, have only mode selector showing
      document.getElementById(nextSelectId).style.display = "none";
      document.getElementById("stationData").style.display = "none";
      document.getElementById("tripData").style.display = "none";
    });

    defaultLogic(modeSelect);

    // Handle date selection
    dateSelect.addEventListener('change', () => {
      const selectedFile = dateSelect.value;
      if (selectedFile) {
        loadJSON(selectedFile);
        document.getElementById(nextSelectId).style.display = "inline";
      }
    });
  });
}

// populates a textbox control with autocomplete, given dataset.
// dataset array of the form [[value, display], [value, display]]
function populateAutocomplete(searchControlId, dataset) {
  const control = document.getElementById(searchControlId);
  control.addEventListener('input', () => {
    const query = control.value.toLowerCase();
    const suggestions = dataset.filter(pair =>
      pair[1].toLowerCase().includes(query)
    );

    // Display suggestions
    const datalist = document.createElement('datalist');
    datalist.id = searchControlId + 'Suggestions';
    suggestions.forEach(([value, display]) => {
      const option = document.createElement('option');
      option.value = value;
      option.textContent = display;
      datalist.appendChild(option);
    });
    control.setAttribute('list', datalist.id);
    document.body.querySelector(`datalist#${datalist.id}`)?.remove();
    document.body.appendChild(datalist);
  });
}