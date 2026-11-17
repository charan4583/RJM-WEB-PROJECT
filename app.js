(function () {
  "use strict";

  var state = {
    roles: [],
    analysis: null,
    selectedRole: null,
    selectedJob: null,
    auth: {
      token: localStorage.getItem("skillbridge-token") || "",
      email: localStorage.getItem("skillbridge-email") || ""
    },
    savedJobs: [],
    otpTimer: null
  };

  var sceneController = null;

  var els = {
    form: document.getElementById("analysisForm"),
    candidateName: document.getElementById("candidateName"),
    companyName: document.getElementById("companyName"),
    targetRole: document.getElementById("targetRole"),
    resumeFile: document.getElementById("resumeFile"),
    resumeText: document.getElementById("resumeText"),
    fileName: document.getElementById("fileName"),
    statusMessage: document.getElementById("statusMessage"),
    loadSampleBtn: document.getElementById("loadSampleBtn"),
    useYourResumeBtn: document.getElementById("useYourResumeBtn"),
    themeToggle: document.getElementById("themeToggle"),
    themeIcon: document.getElementById("themeIcon"),
    savedJobsNav: document.getElementById("savedJobsNav"),
    authNavBtn: document.getElementById("authNavBtn"),
    bestRoleTitle: document.getElementById("bestRoleTitle"),
    bestRoleDetails: document.getElementById("bestRoleDetails"),
    bestRoleScore: document.getElementById("bestRoleScore"),
    bestRoleBar: document.getElementById("bestRoleBar"),
    accuracyMetric: document.getElementById("accuracyMetric"),
    precisionMetric: document.getElementById("precisionMetric"),
    responseMetric: document.getElementById("responseMetric"),
    roleCount: document.getElementById("roleCount"),
    roleList: document.getElementById("roleList"),
    skillCount: document.getElementById("skillCount"),
    skillChips: document.getElementById("skillChips"),
    selectedRoleName: document.getElementById("selectedRoleName"),
    gapList: document.getElementById("gapList"),
    marketBars: document.getElementById("marketBars"),
    jobCount: document.getElementById("jobCount"),
    jobFilter: document.getElementById("jobFilter"),
    jobRoleFilter: document.getElementById("jobRoleFilter"),
    jobList: document.getElementById("jobList"),
    savedJobCount: document.getElementById("savedJobCount"),
    savedJobFilter: document.getElementById("savedJobFilter"),
    savedJobRoleFilter: document.getElementById("savedJobRoleFilter"),
    savedJobList: document.getElementById("savedJobList"),
    learningBtn: document.getElementById("learningBtn"),
    learningPlan: document.getElementById("learningPlan"),
    coverBtn: document.getElementById("coverBtn"),
    coverContext: document.getElementById("coverContext"),
    coverLetter: document.getElementById("coverLetter"),
    copyLetterBtn: document.getElementById("copyLetterBtn"),
    bridgeScene: document.getElementById("bridgeScene")
  };

  function setStatus(message, isError) {
    els.statusMessage.textContent = message;
    els.statusMessage.style.color = isError ? "#e55c5c" : "";
  }

  function formatNumber(value) {
    return new Intl.NumberFormat("en-US").format(value);
  }

  function percent(value) {
    return Math.max(0, Math.min(100, Number(value) || 0));
  }

  function escapeHtml(value) {
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function getThemeColor(name) {
    return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  }

  async function fetchJson(url, options) {
    var response = await fetch(url, options);
    var data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "Request failed.");
    }
    return data;
  }

  function authHeaders() {
    return state.auth.token ? { Authorization: "Bearer " + state.auth.token } : {};
  }

  function setAuth(token, email, savedJobs) {
    state.auth.token = token || "";
    state.auth.email = email || "";
    state.savedJobs = savedJobs || [];
    if (token) {
      localStorage.setItem("skillbridge-token", token);
      localStorage.setItem("skillbridge-email", email);
    } else {
      localStorage.removeItem("skillbridge-token");
      localStorage.removeItem("skillbridge-email");
    }
    updateAuthUI();
    if (state.analysis) {
      renderJobs();
    }
    if (els.savedJobList) {
      renderSavedJobs();
    }
  }

  function updateAuthUI() {
    var loggedIn = Boolean(state.auth.token);
    els.authNavBtn.textContent = loggedIn ? "Logout" : "Login";
    els.savedJobsNav.hidden = !loggedIn;
    if (loggedIn && els.savedJobCount) {
      els.savedJobCount.textContent = state.savedJobs.length + " saved";
    }
  }

  async function hydrateSession() {
    if (!state.auth.token) {
      updateAuthUI();
      return;
    }
    try {
      var data = await fetchJson("/api/me", { headers: authHeaders() });
      setAuth(state.auth.token, data.email, data.savedJobs || []);
    } catch (error) {
      setAuth("", "", []);
    }
  }

  function initTheme() {
    var savedTheme = localStorage.getItem("skillbridge-theme") || "light";
    document.documentElement.setAttribute("data-theme", savedTheme);
    updateThemeButton(savedTheme);

    els.themeToggle.addEventListener("click", function () {
      var current = document.documentElement.getAttribute("data-theme") || "light";
      var next = current === "dark" ? "light" : "dark";
      document.documentElement.setAttribute("data-theme", next);
      localStorage.setItem("skillbridge-theme", next);
      updateThemeButton(next);
      if (sceneController) {
        sceneController.updateColors();
      }
    });
  }

  function updateThemeButton(theme) {
    els.themeIcon.className = theme === "dark" ? "theme-icon icon-sun-fill" : "theme-icon icon-moon-stars-fill";
    els.themeToggle.setAttribute("aria-label", theme === "dark" ? "Switch to light theme" : "Switch to dark theme");
  }

  async function handleLogout() {
    try {
      await fetchJson("/api/logout", { method: "POST", headers: authHeaders() });
    } catch (error) {
      // Local logout can complete even if the server session already expired.
    }
    setAuth("", "", []);
    setStatus("Logged out. You can still analyze resumes, but saving jobs requires login.");
  }

  function initBridgeScene() {
    if (!els.bridgeScene || !window.THREE) {
      return;
    }

    var THREE = window.THREE;
    var canvas = els.bridgeScene;
    var renderer;

    try {
      renderer = new THREE.WebGLRenderer({
        canvas: canvas,
        alpha: true,
        antialias: true
      });
    } catch (error) {
      return;
    }

    canvas.closest(".scene-stage").classList.add("webgl-ready");
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));

    var scene = new THREE.Scene();
    var camera = new THREE.PerspectiveCamera(42, 1, 0.1, 100);
    camera.position.set(0, 2.2, 8.2);

    var group = new THREE.Group();
    scene.add(group);

    var bridgeMaterial = new THREE.MeshStandardMaterial({ metalness: 0.46, roughness: 0.26 });
    var sideMaterial = new THREE.MeshStandardMaterial({ metalness: 0.36, roughness: 0.32 });
    var goldMaterial = new THREE.MeshStandardMaterial({ metalness: 0.42, roughness: 0.22 });
    var materials = [bridgeMaterial, sideMaterial, goldMaterial];

    var planks = [];
    var plankGeometry = new THREE.BoxGeometry(0.78, 0.08, 0.96);
    var railGeometry = new THREE.BoxGeometry(0.08, 0.08, 0.96);
    var towerGeometry = new THREE.BoxGeometry(0.14, 1.2, 0.14);

    for (var i = 0; i < 13; i += 1) {
      var x = (i - 6) * 0.58;
      var y = Math.sin(i * 0.62) * 0.12;
      var z = (i - 6) * -0.08;
      var plank = new THREE.Mesh(plankGeometry, i % 3 === 0 ? goldMaterial : bridgeMaterial);
      plank.position.set(x, y, z);
      plank.rotation.z = Math.sin(i * 0.4) * 0.08;
      group.add(plank);
      planks.push(plank);

      var leftRail = new THREE.Mesh(railGeometry, sideMaterial);
      leftRail.position.set(x, y + 0.22, z - 0.58);
      var rightRail = new THREE.Mesh(railGeometry, sideMaterial);
      rightRail.position.set(x, y + 0.22, z + 0.58);
      group.add(leftRail);
      group.add(rightRail);

      if (i % 3 === 0) {
        var tower = new THREE.Mesh(towerGeometry, sideMaterial);
        tower.position.set(x, y + 0.68, z - 0.7);
        var towerTwo = new THREE.Mesh(towerGeometry, sideMaterial);
        towerTwo.position.set(x, y + 0.68, z + 0.7);
        group.add(tower);
        group.add(towerTwo);
      }
    }

    var panelGeometry = new THREE.BoxGeometry(0.78, 0.42, 0.05);
    var labels = [];
    for (var j = 0; j < 5; j += 1) {
      var panel = new THREE.Mesh(panelGeometry, j % 2 === 0 ? sideMaterial : goldMaterial);
      panel.position.set(-2.2 + j * 1.1, 1.12 + Math.sin(j) * 0.16, -0.95 + j * 0.18);
      panel.rotation.y = -0.42 + j * 0.18;
      group.add(panel);
      labels.push(panel);
    }

    scene.add(new THREE.AmbientLight(0xffffff, 0.72));
    var key = new THREE.DirectionalLight(0xffffff, 1.55);
    key.position.set(3.5, 5, 5);
    scene.add(key);
    var rim = new THREE.PointLight(0x38d98e, 2.2, 12);
    rim.position.set(-3.2, 1.4, 3.2);
    scene.add(rim);

    function updateColors() {
      bridgeMaterial.color = new THREE.Color(getThemeColor("--accent"));
      sideMaterial.color = new THREE.Color(getThemeColor("--accent-2"));
      goldMaterial.color = new THREE.Color(getThemeColor("--gold"));
      rim.color = new THREE.Color(getThemeColor("--accent"));
      materials.forEach(function (material) {
        material.needsUpdate = true;
      });
    }

    function resize() {
      var width = canvas.clientWidth || 600;
      var height = canvas.clientHeight || 360;
      renderer.setSize(width, height, false);
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
    }

    var frame = 0;
    function animate() {
      frame += 0.012;
      group.rotation.x = -0.18 + Math.sin(frame * 0.7) * 0.03;
      group.rotation.y = Math.sin(frame * 0.55) * 0.22;
      planks.forEach(function (plank, index) {
        plank.position.y = Math.sin(index * 0.62) * 0.12 + Math.sin(frame * 2.2 + index) * 0.025;
      });
      labels.forEach(function (panel, index) {
        panel.position.y = 1.12 + Math.sin(index + frame * 1.4) * 0.12;
      });
      resize();
      renderer.render(scene, camera);
      window.requestAnimationFrame(animate);
    }

    updateColors();
    window.addEventListener("resize", resize);
    sceneController = { updateColors: updateColors };
    animate();
  }

  async function loadRoles() {
    try {
      var data = await fetchJson("/api/roles");
      state.roles = data.roles || [];
      state.roles.forEach(function (role) {
        var option = document.createElement("option");
        option.value = role.id;
        option.textContent = role.title;
        els.targetRole.appendChild(option);
      });
    } catch (error) {
      setStatus("Unable to load backend roles. Start the server with python server.py.", true);
    }
  }

  async function loadSampleResume() {
    try {
      setStatus("Loading sample resume...");
      var data = await fetchJson("/api/sample-resume");
      els.resumeText.value = data.resumeText;
      els.candidateName.value = "Siva";
      els.targetRole.value = "agentic-ai-engineer";
      setStatus("Sample resume loaded. You can analyze it now.");
    } catch (error) {
      setStatus(error.message, true);
    }
  }

  function useYourResume() {
    els.candidateName.value = "";
    els.companyName.value = "";
    els.targetRole.value = "";
    els.resumeText.value = "";
    els.resumeFile.value = "";
    els.fileName.textContent = "Readable PDFs and text files are supported.";
    state.analysis = null;
    state.selectedRole = null;
    els.jobList.className = "job-list empty-state";
    els.jobList.textContent = "Analyze a resume to see ranked jobs and application actions.";
    els.roleList.className = "role-list empty-state";
    els.roleList.textContent = "Analyze a resume to rank roles by skill match and market demand.";
    els.skillChips.className = "chip-list empty-state";
    els.skillChips.textContent = "No skills extracted yet.";
    els.gapList.className = "gap-list empty-state";
    els.gapList.textContent = "Select or analyze a role to see missing skills.";
    els.marketBars.className = "market-bars empty-state";
    els.marketBars.textContent = "Demand bars will appear after analysis.";
    els.bestRoleTitle.textContent = "Run an analysis";
    els.bestRoleDetails.textContent = "Skill match, demand weighting, and missing skills will appear here.";
    els.bestRoleScore.textContent = "0%";
    els.bestRoleBar.style.width = "0%";
    els.roleCount.textContent = "0 roles";
    els.skillCount.textContent = "0 found";
    els.jobCount.textContent = "0 jobs";
    setStatus("Fresh resume form ready. Upload a resume, paste resume text, or use both.");
  }

  function buildAnalyzeRequest() {
    var file = els.resumeFile.files[0];
    var commonFields = {
      candidateName: els.candidateName.value.trim(),
      companyName: els.companyName.value.trim(),
      targetRole: els.targetRole.value,
      resumeText: els.resumeText.value.trim()
    };

    if (file) {
      var formData = new FormData();
      Object.keys(commonFields).forEach(function (key) {
        formData.append(key, commonFields[key]);
      });
      formData.append("resumeFile", file);
      return { body: formData };
    }

    return {
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(commonFields)
    };
  }

  async function analyzeResume(event) {
    event.preventDefault();
    var hasFile = Boolean(els.resumeFile.files[0]);
    var hasText = Boolean(els.resumeText.value.trim());
    if (!hasFile && !hasText) {
      setStatus("Paste resume text or upload a resume file first.", true);
      return;
    }

    try {
      setStatus("Analyzing resume, extracting skills, ranking jobs, and preparing application actions...");
      var request = buildAnalyzeRequest();
      var data = await fetchJson("/api/analyze", {
        method: "POST",
        headers: request.headers,
        body: request.body
      });

      state.analysis = data;
      state.selectedRole = data.topMatch;
      state.selectedJob = data.jobMatches && data.jobMatches.length ? data.jobMatches[0] : null;
      renderAnalysis();
      setStatus("Analysis complete. Suitable jobs are ready with apply links and cover-letter buttons.");
    } catch (error) {
      setStatus(error.message, true);
    }
  }

  function renderAnalysis() {
    if (!state.analysis) {
      return;
    }

    var metrics = state.analysis.metrics;
    els.accuracyMetric.textContent = metrics.accuracy + "%";
    els.precisionMetric.textContent = metrics.precision + "%";
    els.responseMetric.textContent = metrics.averageResponse + "s";
    els.roleCount.textContent = state.analysis.roleMatches.length + " roles";
    els.skillCount.textContent = state.analysis.extractedSkills.length + " found";
    els.jobCount.textContent = (state.analysis.jobMatches || []).length + " jobs";
    populateRoleFilter(els.jobRoleFilter, state.analysis.jobMatches || []);

    renderRoles();
    renderSkills();
    renderMarket();
    renderSelectedRole();
    renderJobs();

    els.learningBtn.disabled = false;
    els.coverBtn.disabled = false;
  }

  function renderRoles() {
    var roles = state.analysis.roleMatches;
    els.roleList.classList.remove("empty-state");
    els.roleList.innerHTML = roles
      .map(function (role) {
        var active = state.selectedRole && role.id === state.selectedRole.id ? " active" : "";
        return (
          '<article class="role-card' + active + '">' +
          '<button type="button" data-role-id="' + escapeHtml(role.id) + '">' +
          '<span class="role-topline"><strong>' + escapeHtml(role.title) + "</strong>" +
          '<span class="score-pill">' + role.relevanceScore + "%</span></span>" +
          '<span class="role-meta">' + escapeHtml(role.category) + " | Demand " + formatNumber(role.demand) + " | " + escapeHtml(role.trend) + "</span>" +
          '<span class="mini-bars" aria-hidden="true">' +
          '<span><i style="--bar-width:' + percent(role.matchScore) + '%"></i></span>' +
          '<span><i style="--bar-width:' + percent(role.demandScore) + '%"></i></span>' +
          "</span>" +
          "</button>" +
          "</article>"
        );
      })
      .join("");

    Array.prototype.forEach.call(els.roleList.querySelectorAll("button"), function (button) {
      button.addEventListener("click", function () {
        var roleId = button.getAttribute("data-role-id");
        state.selectedRole = state.analysis.roleMatches.find(function (role) {
          return role.id === roleId;
        });
        renderRoles();
        renderSelectedRole();
        clearGeneratedOutputs();
      });
    });
  }

  function renderSkills() {
    var skills = state.analysis.extractedSkills;
    if (!skills.length) {
      els.skillChips.className = "chip-list empty-state";
      els.skillChips.textContent = "No known technical skills were detected. Add more resume detail and run again.";
      return;
    }

    els.skillChips.className = "chip-list";
    els.skillChips.innerHTML = skills
      .map(function (skill) {
        return '<span class="chip" data-category="' + escapeHtml(skill.category) + '">' + escapeHtml(skill.name) + "</span>";
      })
      .join("");
  }

  function renderMarket() {
    var rows = state.analysis.marketSnapshot;
    if (!rows.length) {
      els.marketBars.className = "market-bars empty-state";
      els.marketBars.textContent = "Demand bars will appear after analysis.";
      return;
    }

    var maxDemand = rows.reduce(function (max, row) {
      return Math.max(max, row.demand);
    }, 1);

    els.marketBars.className = "market-bars";
    els.marketBars.innerHTML = rows
      .slice(0, 6)
      .map(function (row) {
        var width = percent((row.demand / maxDemand) * 100);
        return (
          '<div class="market-row">' +
          "<span>" + escapeHtml(row.role) + "</span>" +
          '<span class="market-track" aria-hidden="true"><i style="--bar-width:' + width + '%"></i></span>' +
          "<small>" + formatNumber(row.demand) + " " + escapeHtml(row.trend) + "</small>" +
          "</div>"
        );
      })
      .join("");
  }

  function renderSelectedRole() {
    var role = state.selectedRole;
    if (!role) {
      return;
    }

    els.bestRoleTitle.textContent = role.title;
    els.bestRoleDetails.textContent =
      role.overlapSkills.length +
      " matched skills, " +
      role.missingSkills.length +
      " gaps, " +
      formatNumber(role.demand) +
      " market demand index.";
    els.bestRoleScore.textContent = role.relevanceScore + "%";
    els.bestRoleBar.style.width = percent(role.relevanceScore) + "%";
    els.selectedRoleName.textContent = role.title;

    if (!role.missingSkills.length) {
      els.gapList.className = "gap-list empty-state";
      els.gapList.textContent = "No required skill gaps found for this role.";
      return;
    }

    els.gapList.className = "gap-list";
    els.gapList.innerHTML = role.missingSkills
      .map(function (skill) {
        return (
          '<div class="gap-item">' +
          "<strong>" + escapeHtml(skill) + "</strong>" +
          '<span class="gap-status">Upskill</span>' +
          "</div>"
        );
      })
      .join("");
  }

  function isJobSaved(jobId) {
    return state.savedJobs.some(function (job) {
      return job.id === jobId;
    });
  }

  function bookmarkIcon(saved) {
    return '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 3h12v18l-6-4-6 4V3z" fill="' + (saved ? "currentColor" : "none") + '" stroke="currentColor" stroke-width="2" stroke-linejoin="round"></path></svg>';
  }

  function jobRoleName(job) {
    return job.roleTitle || job.role || job.title || job.roleId || "Role";
  }

  function exactApplyUrl(job) {
    return job.id ? "apply.html?jobId=" + encodeURIComponent(job.id) : job.applyUrl;
  }

  function populateRoleFilter(selectEl, jobs) {
    var current = selectEl.value;
    var roles = [];
    jobs.forEach(function (job) {
      var role = jobRoleName(job);
      if (role && roles.indexOf(role) === -1) {
        roles.push(role);
      }
    });
    selectEl.innerHTML = '<option value="">All roles</option>' + roles.sort().map(function (role) {
      return '<option value="' + escapeHtml(role) + '">' + escapeHtml(role) + "</option>";
    }).join("");
    selectEl.value = roles.indexOf(current) !== -1 ? current : "";
  }

  function filterJobs(jobs, filterValue, roleValue) {
    var list = jobs.slice();
    if (filterValue === "role" && roleValue) {
      list = list.filter(function (job) {
        return jobRoleName(job) === roleValue;
      });
    }
    if (filterValue === "highSalary") {
      list.sort(function (a, b) {
        return (b.salaryMax || 0) - (a.salaryMax || 0);
      });
    } else if (filterValue === "lowSalary") {
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

  function jobCard(job) {
    var saved = isJobSaved(job.id);
    var missingText = job.missingSkills && job.missingSkills.length ? job.missingSkills.slice(0, 3).join(", ") : "No major gaps";
    return (
      '<article class="job-card">' +
      '<div class="job-topline"><div class="job-title-stack"><strong>' + escapeHtml(job.title) + "</strong>" +
      '<p class="job-company">' + escapeHtml(job.company) + " | " + escapeHtml(job.portal || "Careers") + "</p></div>" +
      '<button class="save-job-btn' + (saved ? " is-saved" : "") + '" type="button" data-save-job-id="' + escapeHtml(job.id) + '" aria-label="' + (saved ? "Remove saved job" : "Save job") + '">' + bookmarkIcon(saved) + "</button></div>" +
      '<div class="job-meta"><span>' + escapeHtml(job.location) + "</span><span>" + escapeHtml(job.salary) + "</span><span>" + escapeHtml(job.workMode) + "</span><span>" + escapeHtml(jobRoleName(job)) + "</span></div>" +
      '<p class="job-summary">' + escapeHtml(job.summary) + "</p>" +
      '<p class="role-meta">Matched: ' + escapeHtml((job.overlapSkills || []).slice(0, 5).join(", ") || "None yet") + "</p>" +
      '<p class="role-meta">Improve: ' + escapeHtml(missingText) + "</p>" +
      '<div class="job-actions"><span class="score-pill">' + (job.matchScore || 0) + "% match</span>" +
      '<a class="apply-link" href="' + escapeHtml(exactApplyUrl(job)) + '" target="_blank" rel="noreferrer">Apply now</a>' +
      '<button class="job-cover-btn" type="button" data-job-id="' + escapeHtml(job.id) + '">Generate cover letter</button></div>' +
      "</article>"
    );
  }

  function attachJobActions(container, jobs) {
    Array.prototype.forEach.call(container.querySelectorAll(".job-cover-btn"), function (button) {
      button.addEventListener("click", function () {
        var job = jobs.find(function (item) {
          return item.id === button.getAttribute("data-job-id");
        });
        createCoverLetter(job);
      });
    });
    Array.prototype.forEach.call(container.querySelectorAll(".save-job-btn"), function (button) {
      button.addEventListener("click", function () {
        var job = jobs.find(function (item) {
          return item.id === button.getAttribute("data-save-job-id");
        });
        toggleSaveJob(job);
      });
    });
  }

  function renderJobs() {
    if (!state.analysis) {
      return;
    }
    var jobs = state.analysis.jobMatches || [];
    els.jobRoleFilter.hidden = els.jobFilter.value !== "role";
    populateRoleFilter(els.jobRoleFilter, jobs);
    var filtered = filterJobs(jobs, els.jobFilter.value, els.jobRoleFilter.value);
    els.jobCount.textContent = filtered.length + " jobs";
    if (!filtered.length) {
      els.jobList.className = "job-list empty-state";
      els.jobList.textContent = "No suitable jobs found for this filter.";
      return;
    }
    els.jobList.className = "job-list";
    els.jobList.innerHTML = filtered.map(jobCard).join("");
    attachJobActions(els.jobList, filtered);
  }

  function renderSavedJobs() {
    if (!els.savedJobList) {
      return;
    }
    if (!state.auth.token) {
      return;
    }
    els.savedJobRoleFilter.hidden = els.savedJobFilter.value !== "role";
    populateRoleFilter(els.savedJobRoleFilter, state.savedJobs);
    var filtered = filterJobs(state.savedJobs, els.savedJobFilter.value, els.savedJobRoleFilter.value);
    els.savedJobCount.textContent = filtered.length + " saved";
    if (!filtered.length) {
      els.savedJobList.className = "job-list empty-state";
      els.savedJobList.textContent = "No saved jobs match this filter.";
      return;
    }
    els.savedJobList.className = "job-list";
    els.savedJobList.innerHTML = filtered.map(jobCard).join("");
    attachJobActions(els.savedJobList, filtered);
  }

  async function toggleSaveJob(job) {
    if (!job) {
      return;
    }
    if (!state.auth.token) {
      setStatus("Please login first to save jobs.", true);
      window.location.href = "login.html";
      return;
    }
    try {
      var response;
      if (isJobSaved(job.id)) {
        response = await fetchJson("/api/saved-jobs/" + encodeURIComponent(job.id), {
          method: "DELETE",
          headers: authHeaders()
        });
      } else {
        response = await fetchJson("/api/saved-jobs", {
          method: "POST",
          headers: Object.assign({ "Content-Type": "application/json" }, authHeaders()),
          body: JSON.stringify({ job: job })
        });
      }
      state.savedJobs = response.savedJobs || [];
      updateAuthUI();
      renderJobs();
      renderSavedJobs();
      setStatus(response.message);
    } catch (error) {
      setStatus(error.message, true);
    }
  }

  function clearGeneratedOutputs() {
    els.learningPlan.className = "learning-plan empty-state";
    els.learningPlan.textContent = "Generate a fresh plan for the selected role.";
    els.coverLetter.textContent = "Your generated cover letter will appear here.";
    els.coverContext.textContent = "Generate a general role letter or choose a job card for a tailored application draft.";
    els.copyLetterBtn.disabled = true;
  }

  async function createLearningPlan() {
    if (!state.selectedRole) {
      setStatus("Analyze a resume first.", true);
      return;
    }

    try {
      els.learningBtn.disabled = true;
      setStatus("Retrieving resources and synthesizing the learning plan...");
      var data = await fetchJson("/api/learning-plan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          roleId: state.selectedRole.id,
          missingSkills: state.selectedRole.missingSkills
        })
      });
      renderLearningPlan(data);
      setStatus("Learning plan generated.");
    } catch (error) {
      setStatus(error.message, true);
    } finally {
      els.learningBtn.disabled = false;
    }
  }

  function renderLearningPlan(plan) {
    els.learningPlan.className = "learning-plan";
    els.learningPlan.innerHTML =
      '<div class="plan-summary"><strong>' +
      escapeHtml(plan.role) +
      "</strong><p>" +
      escapeHtml(plan.summary) +
      "</p></div>" +
      plan.skills
        .map(function (item) {
          var tasks = item.tasks.map(function (task) {
            return "<li>" + escapeHtml(task) + "</li>";
          }).join("");
          var resources = item.resources.map(function (resource) {
            return '<a href="' + escapeHtml(resource.url) + '" target="_blank" rel="noreferrer">' + escapeHtml(resource.title) + "</a>";
          }).join("");
          return (
            '<article class="plan-card">' +
            "<h4>" + escapeHtml(item.skill) + "</h4>" +
            "<p>" + escapeHtml(item.duration) + " | " + escapeHtml(item.objective) + "</p>" +
            "<ul>" + tasks + "</ul>" +
            '<div class="resource-list">' + resources + "</div>" +
            "</article>"
          );
        })
        .join("");
  }

  async function createCoverLetter(job) {
    if (!state.selectedRole || !state.analysis) {
      setStatus("Analyze a resume first.", true);
      return;
    }

    var selectedJob = job || null;
    var roleForLetter = selectedJob
      ? state.analysis.roleMatches.find(function (role) {
          return role.id === selectedJob.roleId;
        }) || state.selectedRole
      : state.selectedRole;

    try {
      els.coverBtn.disabled = true;
      setStatus(selectedJob ? "Drafting cover letter for " + selectedJob.company + "..." : "Drafting cover letter from role context...");
      var data = await fetchJson("/api/cover-letter", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          roleId: roleForLetter.id,
          jobId: selectedJob ? selectedJob.id : "",
          candidateName: els.candidateName.value.trim() || state.analysis.candidate.name,
          company: selectedJob ? selectedJob.company : els.companyName.value.trim() || "Hiring Team",
          jobTitle: selectedJob ? selectedJob.title : roleForLetter.title,
          location: selectedJob ? selectedJob.location : "",
          salary: selectedJob ? selectedJob.salary : "",
          overlapSkills: selectedJob ? selectedJob.overlapSkills : roleForLetter.overlapSkills,
          missingSkills: selectedJob ? selectedJob.missingSkills : roleForLetter.missingSkills
        })
      });
      els.coverLetter.textContent = data.letter;
      els.copyLetterBtn.disabled = false;
      els.coverContext.textContent = selectedJob
        ? "Tailored cover letter for " + selectedJob.title + " at " + selectedJob.company + "."
        : "Role-focused cover letter for " + roleForLetter.title + ".";
      document.getElementById("cover-letter").scrollIntoView({ behavior: "smooth", block: "start" });
      setStatus("Cover letter generated.");
    } catch (error) {
      setStatus(error.message, true);
    } finally {
      els.coverBtn.disabled = false;
    }
  }

  async function copyCoverLetter() {
    try {
      await navigator.clipboard.writeText(els.coverLetter.textContent);
      setStatus("Cover letter copied to clipboard.");
    } catch (error) {
      setStatus("Copy failed. Select the letter text and copy manually.", true);
    }
  }

  function bindEvents() {
    els.form.addEventListener("submit", analyzeResume);
    els.loadSampleBtn.addEventListener("click", loadSampleResume);
    els.useYourResumeBtn.addEventListener("click", useYourResume);
    els.learningBtn.addEventListener("click", createLearningPlan);
    els.coverBtn.addEventListener("click", function () {
      createCoverLetter(null);
    });
    els.copyLetterBtn.addEventListener("click", copyCoverLetter);
    els.resumeFile.addEventListener("change", function () {
      var file = els.resumeFile.files[0];
      els.fileName.textContent = file ? file.name : "Readable PDFs and text files are supported.";
    });
    els.jobFilter.addEventListener("change", renderJobs);
    els.jobRoleFilter.addEventListener("change", renderJobs);
    if (els.savedJobFilter) {
      els.savedJobFilter.addEventListener("change", renderSavedJobs);
      els.savedJobRoleFilter.addEventListener("change", renderSavedJobs);
    }
    els.authNavBtn.addEventListener("click", function () {
      if (state.auth.token) {
        handleLogout();
      } else {
        window.location.href = "login.html";
      }
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    initTheme();
    initBridgeScene();
    bindEvents();
    loadRoles();
    hydrateSession();
  });
}());
