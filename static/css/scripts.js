document.addEventListener("DOMContentLoaded", function() {
  var mainCarousel = document.querySelectorAll('.carousel');
  mainCarousel.forEach(function(c) {
    var bs = bootstrap.Carousel.getOrCreateInstance(c, { interval: 3500, ride: 'carousel' });
  });
});




const faculty = [
{ name: 'DR SAURABH SATYARTH', desig: 'Permanent', dept: 'Dentistry', code: '3444/AMDS', contact: '27035119', exp: '0 yrs' },
{ name: 'DR ABHEET', desig: 'Permanent', dept: 'Dentistry', code: '3531/AMDS', contact: '83050180', exp: '0 yrs' },
{ name: 'DR SHUBHRA KANODIA', desig: 'Assistant Professor', dept: 'AMDS', code: '4346', contact: '43808123', exp: '2 yrs' },
{ name: 'DR SANTOSH KUMAR', desig: 'Permanent', dept: 'Dentistry', code: '3612/AMDS', contact: '45366348', exp: '0 yrs' },
{ name: 'DR SHWETA', desig: 'Permanent', dept: 'Dentistry', code: '2760/AMDS', contact: '83995669', exp: '0 yrs' },
{ name: 'DR AMIT KUMAR SINGH', desig: 'Permanent', dept: 'Dentistry', code: '2947/AMDS', contact: '93481258', exp: '0 yrs' },
{ name: 'Rida Fatima', desig: 'Senior Resident', dept: 'MD - Radio-Diagnosis', code: 'N/A', contact: '90538062', exp: '0 yrs' },
// Additional filler rows to demonstrate pagination
{ name: 'DR EXTRA 1', desig: 'Visiting', dept: 'Dentistry', code: '4001', contact: '90000001', exp: '1 yr' },
{ name: 'DR EXTRA 2', desig: 'Lecturer', dept: 'AMDS', code: '4002', contact: '90000002', exp: '3 yrs' },
{ name: 'DR EXTRA 3', desig: 'Professor', dept: 'Surgery', code: '4003', contact: '90000003', exp: '10 yrs' }
];


// State
let currentPage = 1;
let perPage = parseInt(document.getElementById('perPageSelect').value, 10);


// Elements
const tbody = document.querySelector('#facultyTable tbody');
const pagination = document.getElementById('pagination');
const perPageSelect = document.getElementById('perPageSelect');
const prevBtn = document.getElementById('prevBtn');
const nextBtn = document.getElementById('nextBtn');
const rowsInfo = document.getElementById('rowsInfo');
const showingRange = document.getElementById('showingRange');


function renderTable() {
tbody.innerHTML = '';
const start = (currentPage - 1) * perPage;
const end = Math.min(start + perPage, faculty.length);
const pageItems = faculty.slice(start, end);


for (const f of pageItems) {
const tr = document.createElement('tr');
tr.innerHTML = `<td>${f.name}</td><td>${f.desig}</td><td>${f.dept}</td><td>${f.code}</td><td>${f.contact}</td><td>${f.exp}</td>`;
tbody.appendChild(tr);
}


showingRange.textContent = `${start + 1} - ${end} of ${faculty.length}`;
rowsInfo.textContent = `Page ${currentPage} / ${Math.ceil(faculty.length / perPage)}`;


// enable/disable prev/next
prevBtn.disabled = currentPage === 1;
nextBtn.disabled = end === faculty.length;


renderPagination();
}


function renderPagination() {
pagination.innerHTML = '';
const totalPages = Math.ceil(faculty.length / perPage);
const maxButtons = 5; // how many page buttons to show
let startPage = Math.max(1, currentPage - Math.floor(maxButtons / 2));
let endPage = Math.min(totalPages, startPage + maxButtons - 1);
if (endPage - startPage + 1 < maxButtons) {
startPage = Math.max(1, endPage - maxButtons + 1);
}


/ previous small
const liPrev = document.createElement('li');
liPrev.className = 'page-item' + (currentPage === 1 ? ' disabled' : '');
liPrev.innerHTML = `<button class="page-link" aria-label="Previous small">&laquo;</button>`;
liPrev.addEventListener('click', () => { if (currentPage > 1) { currentPage--; renderTable(); } });
pagination.appendChild(liPrev);


for (let p = startPage; p <= endPage; p++) {
const li = document.createElement('li');
li.className = 'page-item' + (p === currentPage ? ' active' : '');
li.innerHTML = `<button class="page-link">${p}</button>`;
li.addEventListener('click', () => { currentPage = p; renderTable(); });
pagination.appendChild(li);
}


// next small
const liNext = document.createElement('li');
liNext.className = 'page-item' + (currentPage === totalPages ? ' disabled' : '');
liNext.innerHTML = `<button class="page-link" aria-label="Next small">&raquo;</button>`;
liNext.addEventListener('click', () => { if (currentPage < totalPages) { currentPage++; renderTable(); } });
pagination.appendChild(liNext);
}


// Event listeners
perPageSelect.addEventListener('change', (e) => {
perPage = parseInt(e.target.value, 10);
currentPage = 1; // reset to first page
renderTable();
});


prevBtn.addEventListener('click', () => { if (currentPage > 1) { currentPage--; renderTable(); } });
nextBtn.addEventListener('click', () => {
const totalPages = Math.ceil(faculty.length / perPage);
if (currentPage < totalPages) { currentPage++; renderTable(); }
});


// initial render
renderTable();