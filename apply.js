(function () {
  "use strict";

  var selectedJob = null;

  function escapeHtml(value) {
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  async function fetchJson(url) {
    var response = await fetch(url);
    var data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "Request failed.");
    }
    return data;
  }

  function renderJob(job) {
    var card = document.getElementById("applyJobCard");
    card.innerHTML =
      "<h3>" + escapeHtml(job.title) + "</h3>" +
      '<p class="job-company">' + escapeHtml(job.company) + " | " + escapeHtml(job.portal || "Careers") + "</p>" +
      '<div class="job-meta"><span>' + escapeHtml(job.location) + "</span><span>" + escapeHtml(job.salary) + "</span><span>" + escapeHtml(job.workMode) + "</span><span>" + escapeHtml(job.roleTitle) + "</span></div>" +
      '<p class="job-summary">' + escapeHtml(job.summary) + "</p>" +
      '<p class="role-meta">Required skills: ' + escapeHtml((job.skills || []).join(", ")) + "</p>";
    document.getElementById("sourceLink").href = job.sourceUrl || "index.html#jobs";
  }

  async function loadJob() {
    var params = new URLSearchParams(window.location.search);
    var jobId = params.get("jobId");
    if (!jobId) {
      document.getElementById("applyJobCard").textContent = "Job id is missing.";
      return;
    }
    try {
      var data = await fetchJson("/api/jobs/" + encodeURIComponent(jobId));
      selectedJob = data.job;
      renderJob(selectedJob);
    } catch (error) {
      document.getElementById("applyJobCard").textContent = error.message;
    }
  }

  function submitApplication(event) {
    event.preventDefault();
    var form = document.getElementById("applyForm");
    form.reset();
    document.getElementById("applyMessage").textContent = selectedJob
      ? "Application submitted for " + selectedJob.title + " at " + selectedJob.company + "."
      : "Application submitted.";
  }

  document.addEventListener("DOMContentLoaded", function () {
    loadJob();
    document.getElementById("applyForm").addEventListener("submit", submitApplication);
  });
}());
