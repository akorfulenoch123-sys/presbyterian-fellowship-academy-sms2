document.addEventListener("DOMContentLoaded", () => {
  const search = document.querySelector("[data-table-search]");
  if (search) search.addEventListener("input", () => {
    const q = search.value.toLowerCase();
    document.querySelectorAll("tbody tr").forEach(row => {
      row.hidden = !row.innerText.toLowerCase().includes(q);
    });
  });
});
