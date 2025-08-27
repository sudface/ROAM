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