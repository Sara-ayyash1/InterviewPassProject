/**
 * INTERVIEW PASS — CENTRALIZED APPLICATION CONTROLLER
 * ====================================================
 * Modular pattern: each feature is wrapped in an existence check so
 * this single file loads safely on every page without throwing errors.
 */

// ─── UTILITY ────────────────────────────────────────────────────────────────

/**
 * Returns the Django CSRF token from the hidden form input.
 * Required for all POST requests sent via fetch().
 */
function getCSRFToken() {
    const el = document.querySelector('[name=csrfmiddlewaretoken]');
    return el ? el.value : '';
}

// ─── BOOT ───────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {

    initLiveSearch();
    initQuickFilters();
    initQuestionBuilder();
    initNavHighlight();
    initGenerateDescription();
    initGenerateQuestions();
    initAnalyzeCV();

});

// ─── MODULE 1: LIVE SEARCH (Job Seeker — jobs_list page) ────────────────────

/**
 * Real-time job search using the /api/jobs/ endpoint.
 * Rebuilds the job card grid on every keystroke without a page reload.
 */
function initLiveSearch() {
    const searchInput   = document.getElementById('search-input');
    const jobsContainer = document.getElementById('jobs-container');
    if (!searchInput || !jobsContainer) return;

    const appliedJobIds = typeof appliedJobIdsFromServer !== 'undefined'
        ? appliedJobIdsFromServer : [];

    searchInput.addEventListener('input', function () {
        fetch(`/api/jobs/?q=${encodeURIComponent(this.value)}`)
            .then(res => res.status === 401
                ? (window.location.href = '/login/')
                : res.json())
            .then(data => {
                jobsContainer.innerHTML = '';

                if (data.length === 0) {
                    jobsContainer.innerHTML = `
                        <div class="col-span-full py-20 text-center border-2 border-dashed border-gray-200 rounded-2xl">
                            <p class="text-slate-500 font-medium">No jobs matching "${this.value}"</p>
                        </div>`;
                    return;
                }

                data.forEach(job => {
                const isApplied = appliedJobIds.includes(job.id);
                const skillsHTML = job.skills_required
                    ? job.skills_required.split(' ').map(s => 
                        `<span class="px-2 py-0.5 rounded-md bg-slate-50 text-slate-500 text-xs font-medium border border-slate-100/80">${s}</span>`
                    ).join('')
                    : '';

                    jobsContainer.insertAdjacentHTML('beforeend', `
                        <div class="premium-card p-6 flex flex-col gap-4 shadow-premium">
                            <div class="flex justify-between items-center">
                                <span class="badge" style="background:#EFF9F6; color:#32B599;">
                                <svg class="w-3.5 h-3.5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                                        </svg>
                                    ${job.experience_level}
                                </span>
                            </div>
                            <div class="space-y-1.5">
                                <h3 class="font-bold text-gray-900 text-sm leading-snug tracking-tight">${job.title}</h3>
                                <p class="text-sm text-gray-400 leading-relaxed">${job.description.substring(0, 95)}...</p>
                            </div>
                            <div class="space-y-2">
                                <div class="flex items-center gap-1 text-gray-400">
                                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
                                        </svg>
                                    <span class="text-[10px] font-semibold tracking-wider uppercase">Skill Requirements</span>
                                </div>
                                <div class="flex flex-wrap gap-1">${skillsHTML}</div>
                            </div>
                            <div class="mt-auto pt-4 border-t border-slate-50">
                                ${isApplied
                                    ? `<div class="flex items-center justify-center gap-2 w-full py-2.5 px-4 bg-emerald-50 text-emerald-700 rounded-xl text-xs font-bold border border-emerald-100/60">
                                            <svg class="w-4 h-4 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                                            </svg>
                                            Application Secured
                                        </div>`
                                    : `<a href="/jobs/${job.id}/" class="flex items-center justify-center gap-1.5 w-full py-2.5 px-4 bg-gradient-to-r from-[#32B599] to-[#1a8a70] text-white rounded-xl text-xs font-semibold hover:opacity-90 transition">
                                            Apply with Interview Pass
                                            <svg class="w-3.5 h-3.5 transition-transform duration-200 group-hover/btn:translate-x-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M13 5l7 7m0 0l-7 7m7-7H3"/>
                                            </svg>
                                    </a>`
                                }
                            </div>
                        </div>`);
                });
            });
    });
}

function initQuickFilters() {
    const btns = document.querySelectorAll('.quick-filter-btn');
    if (!btns.length) return;

    btns.forEach(btn => {
        btn.addEventListener('click', function () {
            // تحديث الـ active state
            btns.forEach(b => {
                b.classList.remove('bg-primary/10', 'text-primary', 'border-primary/20');
                b.classList.add('bg-gray-50', 'text-gray-500', 'border-gray-100');
            });
            this.classList.remove('bg-gray-50', 'text-gray-500', 'border-gray-100');
            this.classList.add('bg-primary/10', 'text-primary', 'border-primary/20');

            // حط الـ filter بالـ search input وشغّل الـ search
            const searchInput = document.getElementById('search-input');
            if (searchInput) {
                searchInput.value = this.dataset.filter;
                searchInput.dispatchEvent(new Event('input'));
            }
        });
    });
}
// ─── MODULE 2: DYNAMIC QUESTION BUILDER (HR — create_job / edit_job) ────────

/**
 * Lets the HR add or remove custom interview question fields dynamically.
 * Badge numbers update automatically when a row is deleted.
 */
function initQuestionBuilder() {
    const addBtn    = document.getElementById('add-question-btn');
    const container = document.getElementById('questions-container');
    if (!addBtn || !container) return;

    // Recalculate badge numbers after any add/remove
    const updateIndices = () => {
        container.querySelectorAll('.group\\/item').forEach((row, i) => {
            row.querySelector('.q-badge').textContent = i + 1;
        });
    };

    // Inject a new question row when the "Add Question" button is clicked
    addBtn.addEventListener('click', () => {
        const row = document.createElement('div');
        row.className = 'flex gap-3 items-center group/item mt-3';
        row.innerHTML = `
            <span class="q-badge gradient-bg text-white w-7 h-7 rounded-lg flex items-center justify-center text-xs font-bold">0</span>
            <input type="text" name="questions" required placeholder="Type question..."
                class="flex-1 border border-gray-200 rounded-xl px-4 py-3 text-sm focus:ring-2 focus:ring-primary outline-none">
            <button type="button" class="delete-btn text-red-400 hover:text-red-600 px-2">×</button>`;
        container.appendChild(row);
        updateIndices();
    });

    // Event delegation: handle delete clicks on dynamically added rows
    container.addEventListener('click', e => {
        if (e.target.classList.contains('delete-btn')) {
            e.target.closest('.group\\/item').remove();
            updateIndices();
        }
    });
}

// ─── MODULE 3: NAV HIGHLIGHT ────────────────────────────────────────────────

/**
 * Highlights the active nav link based on the current URL path.
 */
function initNavHighlight() {
    const currentPath = window.location.pathname;
    document.querySelectorAll('nav a:not(.logo-link)').forEach(link => {
        const isActive = link.getAttribute('href') === currentPath;
        link.classList.toggle('bg-gray-100', isActive);
        link.classList.toggle('text-gray-900', isActive);
        if (!isActive && !link.classList.contains('gradient-bg')) {
            link.classList.add('text-gray-500');
        }
    });
}

// ─── MODULE 4: AI GENERATE DESCRIPTION (HR — create_job / edit_job) ─────────

/**
 * Calls the /hr/jobs/ai/generate-description/ endpoint and populates
 * the description textarea with the AI-generated text.
 * Validates that title and skills are filled before sending the request.
 */
function initGenerateDescription() {
    const btn      = document.getElementById('generate-description-btn');
    const errorMsg = document.getElementById('ai-error-msg');
    if (!btn) return;

    btn.addEventListener('click', async () => {
        const title      = document.querySelector('input[name="title"]').value.trim();
        const skills     = document.querySelector('input[name="skills_required"]').value.trim();
        const experience = document.querySelector('select[name="experience_level"]').value;

        // Show inline error if required fields are empty
        if (!title || !skills) {
            errorMsg.style.display = 'block';
            return;
        }
        errorMsg.style.display = 'none';

        btn.disabled    = true;
        btn.textContent = 'Generating...';

        try {
            const res = await fetch('/hr/jobs/ai/generate-description/', {
                method: 'POST',
                headers: { 'X-CSRFToken': getCSRFToken() },
                body: new URLSearchParams({ title, skills_required: skills, experience_level: experience }),
            });

            if (res.status === 429) {
                alert('AI daily limit reached. Please try again tomorrow!');
            } else if (!res.ok) {
                alert('Something went wrong. Please try again.');
            } else {
                const data = await res.json();
                if (data.description) {
                    document.querySelector('textarea[name="description"]').value = data.description;
                }
            }
        } catch {
            alert('Failed to connect to the server.');
        } finally {
            btn.disabled    = false;
            btn.textContent = 'Generate Description with AI';
        }
    });
}

// ─── MODULE 5: AI GENERATE QUESTIONS (HR — create_job / edit_job) ───────────

/**
 * Calls the /hr/jobs/ai/generate-questions/ endpoint and replaces
 * the current question inputs with the AI-suggested questions.
 */
function initGenerateQuestions() {
    const btn = document.getElementById('generate-questions-btn');
    const errorMsg = document.getElementById('ai-qerror-msg');
    if (!btn) return;

    btn.addEventListener('click', async () => {
        const title      = document.querySelector('input[name="title"]').value.trim();
        const skills     = document.querySelector('input[name="skills_required"]').value.trim();
        const experience = document.querySelector('select[name="experience_level"]').value;

        if (!title || !skills) {
            errorMsg.style.display = 'block';
            return;
        }
        errorMsg.style.display = 'none';

        btn.disabled    = true;
        btn.textContent = 'Generating...';

        try {
            const res = await fetch('/hr/jobs/ai/generate-questions/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': getCSRFToken(),
                },
                body: new URLSearchParams({ title, skills_required: skills, experience_level: experience }),
            });

            const data = await res.json();

            if (data.questions) {
                const container = document.getElementById('questions-container');
                container.innerHTML = '';

                // Rebuild the question rows with AI-generated content
                data.questions.forEach((q, i) => {
                    container.insertAdjacentHTML('beforeend', `
                        <div class="flex gap-2.5 items-center group/item">
                            <span class="q-badge gradient-bg text-white text-[10px] font-extrabold w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0">${i + 1}</span>
                            <div class="relative w-full">
                                <input type="text" name="questions" required value="${q}"
                                    class="w-full pl-4 pr-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary bg-slate-50/40 text-xs font-semibold text-slate-800 shadow-inner transition">
                            </div>
                            <button type="button" class="delete-btn text-red-400 hover:text-red-600 px-2">×</button>
                        </div>`);
                });

                // Update the questions counter badge
                const indicator = document.getElementById('questions-indicator');
                if (indicator) indicator.textContent = `${data.questions.length} Questions Active`;
            } else {
                alert('Could not generate questions. Please try again.');
            }
        } catch {
            alert('Failed to connect to the server.');
        } finally {
            btn.disabled    = false;
            btn.textContent = 'Generate Questions with AI';
        }
    });
}

// ─── MODULE 6: AI ANALYZE CV (HR — applicant_profile page) ──────────────────

/**
 * Calls the analyze-cv endpoint for the current applicant and renders
 * the match score, strengths, gaps, and summary into the result box.
 * The applicant ID is injected by Django via a data attribute on the button.
 */
function initAnalyzeCV() {
    const btn       = document.getElementById('analyze-cv-btn');
    const resultBox = document.getElementById('cv-analysis-result');
    if (!btn || !resultBox) return;

    btn.addEventListener('click', async () => {
        const applicantId = btn.dataset.applicantId;

        btn.disabled    = true;
        btn.textContent = 'Analyzing...';

        try {
            const res  = await fetch(`/hr/applicants/${applicantId}/analyze-cv/`);
            const data = await res.json();

            resultBox.classList.remove('hidden');

            if (data.error) {
                resultBox.innerHTML = `<p class="text-red-500 text-sm">${data.error}</p>`;
                return;
            }

            // Render structured analysis result
            resultBox.innerHTML = `
                <div class="flex items-center gap-3 mb-2">
                    <span class="text-2xl font-extrabold text-primary">${data.match_score}%</span>
                    <span class="text-xs text-gray-500 font-medium">Match Score</span>
                </div>
                <div>
                    <p class="text-xs font-semibold text-gray-400 uppercase mb-1">Strengths</p>
                    <p class="text-sm text-gray-700">${data.strengths.join(', ')}</p>
                </div>
                <div>
                    <p class="text-xs font-semibold text-gray-400 uppercase mb-1">Gaps</p>
                    <p class="text-sm text-gray-700">${data.gaps.join(', ') || 'None identified'}</p>
                </div>
                <div>
                    <p class="text-xs font-semibold text-gray-400 uppercase mb-1">Summary</p>
                    <p class="text-sm text-gray-700">${data.summary}</p>
                </div>`;
        } catch {
            resultBox.classList.remove('hidden');
            resultBox.innerHTML = `<p class="text-red-500 text-sm">Failed to connect to the server.</p>`;
        } finally {
            btn.disabled    = false;
            btn.textContent = ' Analyze CV';
        }
    });
}