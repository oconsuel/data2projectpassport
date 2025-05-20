document.addEventListener('DOMContentLoaded', function() {
	// Bootstrap tooltips
	document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(function(el) {
		if (window.bootstrap) new bootstrap.Tooltip(el);
	});

	// Рекомендации от ИИ
	function fetchAndRenderRecommendations(projectId) {
		const block = document.getElementById("recommendation-block");
		["recommend-btn", "regenerate-recommend-btn"].forEach(id => {
			const btn = document.getElementById(id);
			if (btn) btn.setAttribute("disabled", "");
		});
		block.querySelector("#loading")?.remove();
		block.insertAdjacentHTML("beforeend",
			`<p id="loading" class="text-muted mt-2">Генерация...</p>`
		);
		fetch(`/recommend/${projectId}`, { method: "POST" })
			.then(resp => resp.json())
			.then(data => {
				if (data.error) {
					block.innerHTML = `
						<p class="text-danger">${data.error}</p>
						<button id="recommend-btn" class="btn btn-outline-primary" data-project-id="${projectId}">Повторить</button>
					`;
				} else {
					const rec = data.recommendations;
					const safeReplace = (text) => (typeof text === 'string' ? text.replace(/\n/g, '<br/>') : String(text || ''));
					block.innerHTML = `
						<p>
							<strong>Краткое описание:</strong>
							<i class="bi bi-info-circle" data-bs-toggle="tooltip" title="${rec.summary_short_reason}"></i><br>
							${rec.summary_short}
						</p>
						<p>
							<strong>Подробное описание:</strong>
							<i class="bi bi-info-circle" data-bs-toggle="tooltip" title="${rec.summary_long_reason}"></i><br>
						</p>
						<p>#1 Цель<br>${safeReplace(rec.summary_long.goal)}</p>
						<p>#2 Задачи<br>${safeReplace(rec.summary_long.tasks)}</p>
						<p>#3 Актуальность<br>${safeReplace(rec.summary_long.relevance)}</p>
						<p>#4 Ожидаемый результат<br>${safeReplace(rec.summary_long.expected_result)}</p>
						<p><strong>Теги:</strong>
							<i class="bi bi-info-circle" data-bs-toggle="tooltip" title="${rec.tags_reason}"></i>
						</p>
						<div>
							${(rec.tags || []).map(tag => `<span class="tag">${tag}</span>`).join('')}
						</div>
						<button id="regenerate-recommend-btn" class="btn btn-outline-secondary mt-3">Повторить генерацию рекомендаций</button>
					`;
				}
			})
			.catch(err => {
				block.innerHTML = `
					<p class="text-danger">Ошибка при генерации рекомендаций: ${err.message}</p>
					<button id="regenerate-recommend-btn" class="btn btn-outline-secondary mt-3">Повторить генерацию рекомендаций</button>
				`;
			})
			.finally(() => {
				document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => {
					if (window.bootstrap) new bootstrap.Tooltip(el);
				});
				attachRecommendListeners();
			});
	}
	function attachRecommendListeners() {
		const projectId = document.getElementById("recommendation-block")?.dataset.projectId;
		document.getElementById("recommend-btn")?.addEventListener("click", function() {
			fetchAndRenderRecommendations(projectId);
		});
		document.getElementById("regenerate-recommend-btn")?.addEventListener("click", function() {
			fetchAndRenderRecommendations(projectId);
		});
	}
	attachRecommendListeners();

	// Постер: показать/скрыть, обработка редактирования и статуса
	function checkPosterStatus(projectId, maxAttempts = 10, attempt = 1) {
		if (attempt > maxAttempts) {
			const loader = document.getElementById('poster-loader');
			if (loader) loader.innerHTML = '<p class="text-danger">Ошибка загрузки постера. Попробуйте обновить страницу.</p>';
			return;
		}
		fetch(`/poster-status/${projectId}`)
			.then(response => response.json())
			.then(data => {
				if (data.poster_path) {
					const loader = document.getElementById('poster-loader');
					const image = document.getElementById('poster-image');
					const actions = document.getElementById('poster-actions');
					if (loader && image && actions) {
						loader.classList.remove('show');
						image.src = `/${data.poster_path}`;
						image.classList.remove('hidden');
						actions.classList.remove('hidden');
					}
				} else {
					setTimeout(() => checkPosterStatus(projectId, maxAttempts, attempt + 1), 2000);
				}
			})
			.catch(() => setTimeout(() => checkPosterStatus(projectId, maxAttempts, attempt + 1), 2000));
	}
	const projectData = document.getElementById('project-data');
	let projectId = null;
	if (projectData) {
		projectId = parseInt(projectData.dataset.projectId, 10);
		const posterPath = projectData.dataset.posterPath === "null" ? null : projectData.dataset.posterPath;
		const projectStatus = projectData.dataset.status;
		if (projectStatus === "done") {
			checkPosterStatus(projectId, 10);
		}
	}
	// Кнопка "Изменить постер" — с wizard modal
	const editPosterBtn = document.getElementById('edit-poster-btn');
	const editPosterForm = document.getElementById('edit-poster-form');
	editPosterBtn?.addEventListener('click', function() {
		if (typeof dialogGraph !== 'undefined' && dialogGraph) {
			showWizardStep("start");
			document.getElementById('wizard-modal').classList.add("show");
		} else {
			editPosterForm?.classList.toggle('hidden');
			document.getElementById('poster-comment')?.focus();
		}
	});
	// Кнопка "Отправить комментарий" (быстрый режим без wizard)
	document.getElementById('submit-comment-btn')?.addEventListener('click', async function() {
		const comment = document.getElementById('poster-comment').value.trim();
		if (!comment) return alert('Пожалуйста, введите комментарий.');
		const loader = document.getElementById('poster-loader');
		const image = document.getElementById('poster-image');
		const actions = document.getElementById('poster-actions');
		if (loader && image && actions) {
			loader.classList.add('show');
			image.classList.add('hidden');
			actions.classList.add('hidden');
		}
		try {
			const response = await fetch(`/regenerate-poster/${projectId}`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ comment })
			});
			const data = await response.json();
			if (data.error) throw new Error(data.error);
			checkPosterStatus(projectId, 10);
		} catch (error) {
			loader.innerHTML = `<p class="text-danger">Ошибка: ${error.message}</p>`;
		}
	});

	// Dropzone drag-n-drop
	const dropzone = document.getElementById('file-dropzone');
	const fileInput = document.getElementById('file-input');
	const fileList = document.getElementById('file-list');
	dropzone.onclick = function(e) {
		if (e.target.tagName !== "INPUT") fileInput.click();
	};
	dropzone.addEventListener('dragover', function(e) {
		e.preventDefault(); dropzone.classList.add('dragover');
	});
	dropzone.addEventListener('dragleave', function(e) {
		e.preventDefault(); dropzone.classList.remove('dragover');
	});
	dropzone.addEventListener('drop', function(e) {
		e.preventDefault(); dropzone.classList.remove('dragover');
		fileInput.files = e.dataTransfer.files;
		updateFileList();
	});
	fileInput.onchange = updateFileList;
	function updateFileList() {
		let files = fileInput.files;
		let names = [];
		for (let i = 0; i < files.length; i++) names.push(files[i].name);
		fileList.innerHTML = names.length ? "Выбрано файлов: " + names.join(', ') : "";
	}

	// --- Wizard Modal для генерации постера ---
	// dialogGraph должен быть определён в window/dialogGraph (например, в HTML до подключения скрипта!)
	let wizardAnswers = {};
	let wizardStack = [];
	let userBranches = [];
	window.showWizardStep = function(step) {
		const modal = document.getElementById('wizard-modal');
		modal.innerHTML = `
			<div style="background:#fff; padding:30px 20px 20px 20px; border-radius:12px; min-width:320px; max-width:95vw; max-height:90vh; overflow:auto; position:relative;">
				<button style="position:absolute;top:10px;right:15px;font-size:22px;line-height:1;border:none;background:none;" onclick="document.getElementById('wizard-modal').classList.remove('show')">&times;</button>
				<div id="wizard-content"></div>
			</div>
		`;
		const content = document.getElementById('wizard-content');
		const data = dialogGraph[step];
		if (!data) return;
		let html = `<h4>${data.question || ''}</h4>`;
		if (step === "start") {
			html += '<form id="start-form">';
			for (const key in data.options) {
				html += `<label><input type="checkbox" name="option" value="${key}"> ${data.options[key]}</label><br>`;
			}
			html += `<button type="submit" class="btn btn-primary mt-2">Далее</button></form>`;
			content.innerHTML = html;
			document.getElementById('start-form').onsubmit = function(e) {
				e.preventDefault();
				userBranches = Array.from(document.querySelectorAll('input[name="option"]:checked')).map(x => x.value);
				wizardStack = ["start"];
				wizardAnswers = {};
				if (userBranches.length === 0) return;
				nextBranch(0);
			};
			return;
		}
		if (data.options) {
			html += '<form id="branch-form">';
			for (const key in data.options) {
				html += `<label><input type="checkbox" name="option" value="${key}"> ${data.options[key]}</label><br>`;
			}
			if (data.comment) {
				html += '<textarea name="comment" class="form-control mt-2" placeholder="Комментарий"></textarea><br>';
			}
			html += `<button type="submit" class="btn btn-primary mt-2">Далее</button>`;
			if (data.back) {
				html += `<button type="button" class="btn btn-secondary mt-2 ms-2" id="wizard-back">Назад</button>`;
			}
			html += '</form>';
			content.innerHTML = html;
			document.getElementById('branch-form').onsubmit = function(e) {
				e.preventDefault();
				const selected = Array.from(document.querySelectorAll('input[name="option"]:checked')).map(x => x.value);
				const comment = document.querySelector('textarea') ? document.querySelector('textarea').value : "";
				wizardAnswers[step] = {"selected": selected, "comment": comment};
				wizardStack.push(step);
				nextBranch(userBranches.indexOf(step)+1);
			};
			if (data.back) {
				document.getElementById('wizard-back').onclick = function() {
					if (wizardStack.length > 1) {
						wizardStack.pop();
						showWizardStep(wizardStack[wizardStack.length-1]);
					} else {
						showWizardStep("start");
					}
				};
			}
			return;
		}
		if (data.input === "text") {
			html += '<form id="text-form">';
			html += `<textarea name="text" class="form-control mt-2" placeholder="Комментарий"></textarea><br>`;
			html += `<button type="submit" class="btn btn-primary mt-2">Создать новый постер</button>`;
			if (data.back) {
				html += `<button type="button" class="btn btn-secondary mt-2 ms-2" id="wizard-back">Назад</button>`;
			}
			html += '</form>';
			content.innerHTML = html;
			document.getElementById('text-form').onsubmit = function(e) {
				e.preventDefault();
				wizardAnswers[step] = {"text": document.querySelector('textarea').value};
				wizardStack.push(step);
				if (step === "final") {
					submitWizard();
				} else {
					nextBranch(userBranches.indexOf(step)+1);
				}
			};
			if (data.back) {
				document.getElementById('wizard-back').onclick = function() {
					if (wizardStack.length > 1) {
						wizardStack.pop();
						showWizardStep(wizardStack[wizardStack.length-1]);
					} else {
						showWizardStep("start");
					}
				};
			}
			return;
		}
	};
	function nextBranch(index) {
		if (index < userBranches.length) {
			showWizardStep(userBranches[index]);
		} else {
			showWizardStep("final");
		}
	}
	function submitWizard() {
		document.getElementById('wizard-modal').classList.remove("show");
		const loader = document.getElementById('poster-loader');
		const image = document.getElementById('poster-image');
		const actions = document.getElementById('poster-actions');
		if (loader && image && actions) {
			loader.classList.add('show');
			image.classList.add('hidden');
			actions.classList.add('hidden');
		}
		const projectId = document.getElementById('project-data').getAttribute('data-project-id');
		fetch(`/projects/${projectId}/poster-dialog`, {
			method: "POST",
			headers: {"Content-Type": "application/json"},
			body: JSON.stringify(wizardAnswers)
		})
		.then(res => res.json())
		.then(data => {
			loader.classList.remove('show');
			alert("Новый постер создан. Обновите страницу или нажмите ОК.");
			if (data.poster_path) {
				const img = document.getElementById('poster-image');
				img.src = "/" + data.poster_path + "?" + new Date().getTime();
				img.classList.remove('hidden');
				document.getElementById('poster-actions').classList.remove('hidden');
			}
		})
		.catch(error => {
			loader.innerHTML = `<p class="text-danger">Ошибка: ${error.message}</p>`;
		});
	}
});
