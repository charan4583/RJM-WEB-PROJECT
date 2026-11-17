(function () {
  "use strict";

  var savedJobs = [];
  var els = {
    count: document.getElementById("savedJobCount"),
    filter: document.getElementById("savedJobFilter"),
    roleFilter: document.getElementById("savedJobRoleFilter"),
    list: document.getElementById("savedJobList")
  };

  async function fetchJson(url, options) {
    var response = await fetch(url, options);
    var data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "Request failed.");
    }
    return data;
  }

  function escapeHtml(value) {
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function jobRoleName(job) {
    return job.roleTitle || job.role || job.title || job.roleId || "Role";
  }

  function exactApplyUrl(job) {
    return job.id ? "apply.html?jobId=" + encodeURIComponent(job.id) : job.applyUrl;
  }

  function populateRoleFilter() {
    var current = els.roleFilter.value;
    var roles = [];
    savedJobs.forEach(function (job) {
      var role = jobRoleName(job);
      if (role && roles.indexOf(role) === -1) {
        roles.push(role);
      }
    });
    els.roleFilter.innerHTML = '<option value="">All roles</option>' + roles.sort().map(function (role) {
      return '<option value="' + escapeHtml(role) + '">' + escapeHtml(role) + "</option>";
    }).join("");
    els.roleFilter.value = roles.indexOf(current) !== -1 ? current : "";
  }

  function filterJobs() {
    var list = savedJobs.slice();
    var filter = els.filter.value;
    if (filter === "role" && els.roleFilter.value) {
      list = list.filter(function (job) {
        return jobRoleName(job) === els.roleFilter.value;
      });
    }
    if (filter === "highSalary") {
      list.sort(function (a, b) {
        return (b.salaryMax || 0) - (a.salaryMax || 0);
      });
    } else if (filter === "lowSalary") {
      list.sort(function (a, b) {
        return (a.salaryMin || 0) - (b.salaryMin || 0);
      });
    } else {
      list.sort(function (a, b) {
        return (b.matchScore || 0) - (a.matchScore || 0);
      });
    }
    return list;
  }

  function bookmarkIcon() {
    return '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 3h12v18l-6-4-6 4V3z" fill="currentColor" stroke="currentColor" stroke-width="2" stroke-linejoin="round"></path></svg>';
  }

  function jobCard(job) {
    var missingText = job.missingSkills && job.missingSkills.length ? job.missingSkills.slice(0, 3).join(", ") : "No major gaps";
    return (
      '<article class="job-card">' +
      '<div class="job-topline"><div class="job-title-stack"><strong>' + escapeHtml(job.title) + "</strong>" +
      '<p class="job-company">' + escapeHtml(job.company) + " | " + escapeHtml(job.portal || "Careers") + "</p></div>" +
      '<button class="save-job-btn is-saved" type="button" data-remove-job-id="' + escapeHtml(job.id) + '" aria-label="Remove saved job">' + bookmarkIcon() + "</button></div>" +
      '<div class="job-meta"><span>' + escapeHtml(job.location) + "</span><span>" + escapeHtml(job.salary) + "</span><span>" + escapeHtml(job.workMode) + "</span><span>" + escapeHtml(jobRoleName(job)) + "</span></div>" +
      '<p class="job-summary">' + escapeHtml(job.summary) + "</p>" +
      '<p class="role-meta">Matched: ' + escapeHtml((job.overlapSkills || []).slice(0, 5).join(", ") || "None yet") + "</p>" +
      '<p class="role-meta">Improve: ' + escapeHtml(missingText) + "</p>" +
      '<div class="job-actions"><span class="score-pill">' + (job.matchScore || 0) + "% match</span>" +
      '<a class="apply-link" href="' + escapeHtml(exactApplyUrl(job)) + '" target="_blank" rel="noreferrer">Apply now</a></div>' +
      "</article>"
    );
  }

  function render() {
    populateRoleFilter();
    els.roleFilter.hidden = els.filter.value !== "role";
    var filtered = filterJobs();
    els.count.textContent = filtered.length + " saved";
    if (!filtered.length) {
      els.list.className = "job-list empty-state";
      els.list.textContent = "No saved jobs match this filter.";
      return;
    }
    els.list.className = "job-list";
    els.list.innerHTML = filtered.map(jobCard).join("");
    Array.prototype.forEach.call(els.list.querySelectorAll(".save-job-btn"), function (button) {
      button.addEventListener("click", function () {
        removeJob(button.getAttribute("data-remove-job-id"));
      });
    });
  }

  async function removeJob(jobId) {
    var data = await fetchJson("/api/saved-jobs/" + encodeURIComponent(jobId), {
      method: "DELETE",
      headers: window.SkillBridgeCommon.authHeaders()
    });
    savedJobs = data.savedJobs || [];
    render();
  }

  async function loadSavedJobs() {
    if (!window.SkillBridgeCommon.getToken()) {
      window.location.href = "login.html";
      return;
    }
    try {
      var data = await fetchJson("/api/saved-jobs", {
        headers: window.SkillBridgeCommon.authHeaders()
      });
      savedJobs = data.savedJobs || [];
      render();
    } catch (error) {
      els.list.className = "job-list empty-state";
      els.list.textContent = error.message;
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    els.filter.addEventListener("change", render);
    els.roleFilter.addEventListener("change", render);
    loadSavedJobs();
  });
}());
