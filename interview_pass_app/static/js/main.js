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
                    jobsContainer.insertAdjacentHTML('beforeend', `
                        <div class="bg-white rounded-2xl p-6 border border-gray-100 hover:shadow-lg transition-all">
                            <h3 class="font-bold text-gray-900">${job.title}</h3>
                            <p class="text-sm text-slate-600 mt-2">${job.description.substring(0, 100)}...</p>
                            <div class="mt-4">
                                ${isApplied
                                    ? '<div class="text-emerald-600 font-bold text-xs bg-emerald-50 py-2 rounded-lg text-center">Application Secured</div>'
                                    : `<a href="/jobs/${job.id}/" class="block bg-primary text-white text-center py-2 rounded-lg text-xs font-bold hover:opacity-90">Apply Now</a>`}
                            </div>
                        </div>`);
                });
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
    if (!btn) return;

    btn.addEventListener('click', async () => {
        const title      = document.querySelector('input[name="title"]').value.trim();
        const skills     = document.querySelector('input[name="skills_required"]').value.trim();
        const experience = document.querySelector('select[name="experience_level"]').value;

        if (!title || !skills) {
            alert('Please fill in the Job Title and Skills first.');
            return;
        }

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