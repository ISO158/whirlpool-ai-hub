// Configuração da URL da API (relativa se rodando no mesmo host, ou configurável para deploy externo)
const API_BASE = window.location.origin;

// Estado da Aplicação
let selectedFile = null;
let recordedBlob = null;
let mediaRecorder = null;
let audioChunks = [];
let timerInterval = null;
let secondsRecorded = 0;
let lastReportData = null;

// Elementos do DOM
const btnRecord = document.getElementById('btnRecord');
const btnStopRecord = document.getElementById('btnStopRecord');
const recordTimer = document.getElementById('recordTimer');
const audioPreview = document.getElementById('audioPreview');

const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const btnBrowse = document.getElementById('btnBrowse');
const fileNameDisplay = document.getElementById('fileNameDisplay');
const deptSelect = document.getElementById('deptSelect');

const btnProcess = document.getElementById('btnProcess');
const processingStatus = document.getElementById('processingStatus');
const resultsSection = document.getElementById('resultsSection');

// Elementos de Compartilhamento
const btnShareWhatsApp = document.getElementById('btnShareWhatsApp');
const btnShareEmail = document.getElementById('btnShareEmail');
const btnCopyReport = document.getElementById('btnCopyReport');

// Elementos de RAG
const ragInput = document.getElementById('ragInput');
const btnRagAsk = document.getElementById('btnRagAsk');
const ragResponseArea = document.getElementById('ragResponseArea');
const ragAnswerText = document.getElementById('ragAnswerText');
const ragSourcesList = document.getElementById('ragSourcesList');

// 1. Gravação de Áudio via Navegador (MediaRecorder API)
btnRecord.addEventListener('click', async () => {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];

        mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                audioChunks.push(event.data);
            }
        };

        mediaRecorder.onstop = () => {
            recordedBlob = new Blob(audioChunks, { type: 'audio/webm' });
            selectedFile = null; // Prioriza gravação
            fileNameDisplay.textContent = `🎙️ Áudio gravado pronto (${(recordedBlob.size / 1024).toFixed(1)} KB)`;
            audioPreview.src = URL.createObjectURL(recordedBlob);
            audioPreview.style.display = 'block';
            btnProcess.disabled = false;
        };

        mediaRecorder.start();
        btnRecord.style.display = 'none';
        btnStopRecord.style.display = 'inline-flex';
        recordTimer.style.display = 'block';
        secondsRecorded = 0;
        recordTimer.textContent = '00:00';
        timerInterval = setInterval(() => {
            secondsRecorded++;
            const mins = String(Math.floor(secondsRecorded / 60)).padStart(2, '0');
            const secs = String(secondsRecorded % 60).padStart(2, '0');
            recordTimer.textContent = `${mins}:${secs}`;
        }, 1000);

    } catch (err) {
        alert('Não foi possível acessar o microfone. Verifique as permissões do seu navegador.');
        console.error(err);
    }
});

btnStopRecord.addEventListener('click', () => {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
        mediaRecorder.stream.getTracks().forEach(track => track.stop());
        clearInterval(timerInterval);
        btnStopRecord.style.display = 'none';
        btnRecord.style.display = 'inline-flex';
    }
});

// 2. Upload de Arquivos
btnBrowse.addEventListener('click', () => fileInput.click());

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleFileSelect(e.target.files[0]);
    }
});

dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.style.borderColor = 'var(--whirlpool-blue)';
});

dropZone.addEventListener('dragleave', () => {
    dropZone.style.borderColor = 'var(--border-color)';
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.style.borderColor = 'var(--border-color)';
    if (e.dataTransfer.files.length > 0) {
        handleFileSelect(e.dataTransfer.files[0]);
    }
});

function handleFileSelect(file) {
    selectedFile = file;
    recordedBlob = null;
    audioPreview.style.display = 'none';
    fileNameDisplay.textContent = `📁 Arquivo selecionado: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
    btnProcess.disabled = false;
}

// 3. Processamento com Agentes de IA
btnProcess.addEventListener('click', async () => {
    if (!selectedFile && !recordedBlob) {
        alert('Selecione um arquivo ou faça uma gravação primeiro.');
        return;
    }

    btnProcess.disabled = true;
    processingStatus.style.display = 'flex';
    resultsSection.style.display = 'none';

    const formData = new FormData();
    const department = deptSelect.value;
    formData.append('department', department);

    if (recordedBlob) {
        formData.append('file', recordedBlob, 'gravacao_microfone.webm');
    } else {
        formData.append('file', selectedFile);
    }

    try {
        const response = await fetch(`${API_BASE}/api/process-audio`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const errData = await response.json();
            throw new Error(errData.detail || 'Falha ao processar áudio');
        }

        const data = await response.json();
        lastReportData = data;
        renderResults(data);

    } catch (err) {
        alert(`Erro durante o processamento: ${err.message}`);
        console.error(err);
    } finally {
        processingStatus.style.display = 'none';
        btnProcess.disabled = false;
    }
});

// 4. Renderização dos Resultados
async function renderResults(data) {
    document.getElementById('reportTitle').textContent = data.title;
    document.getElementById('reportDept').textContent = data.department;
    document.getElementById('reportId').textContent = data.meeting_id;
    document.getElementById('reportSummary').textContent = data.summary;

    // Participantes
    const partsContainer = document.getElementById('reportParticipants');
    partsContainer.innerHTML = '';
    (data.participants || []).forEach(p => {
        const tag = document.createElement('span');
        tag.className = 'participant-tag';
        tag.textContent = `👤 ${p}`;
        partsContainer.appendChild(tag);
    });

    // Transcrição Sanitizada
    document.getElementById('reportTranscription').textContent = data.sanitized_transcription;

    // Renderização do Diagrama Mermaid
    const mermaidContainer = document.getElementById('mermaidContainer');
    mermaidContainer.innerHTML = `<div class="mermaid">${data.mermaid_code}</div>`;
    try {
        await mermaid.run({ nodes: mermaidContainer.querySelectorAll('.mermaid') });
    } catch (mermaidErr) {
        console.warn('Erro ao renderizar Mermaid:', mermaidErr);
        mermaidContainer.innerHTML = `<pre style="text-align: left; font-size: 0.85rem;"><code>${data.mermaid_code}</code></pre>`;
    }

    // Renderização da Matriz RACI
    const raciContainer = document.getElementById('raciTableContainer');
    raciContainer.innerHTML = parseMarkdownTable(data.raci_markdown);

    // Exibe a seção de resultados
    resultsSection.style.display = 'flex';
    resultsSection.scrollIntoView({ behavior: 'smooth' });
}

// Converte Markdown Table simples em HTML Table
function parseMarkdownTable(markdown) {
    const lines = markdown.trim().split('\n').filter(l => l.includes('|'));
    if (lines.length < 2) return `<pre>${markdown}</pre>`;

    let html = '<table><thead><tr>';
    const headers = lines[0].split('|').map(s => s.trim()).filter(Boolean);
    headers.forEach(h => html += `<th>${h}</th>`);
    html += '</tr></thead><tbody>';

    for (let i = 2; i < lines.length; i++) {
        const cells = lines[i].split('|').map(s => s.trim()).filter(Boolean);
        if (cells.length === 0) continue;
        html += '<tr>';
        cells.forEach(c => html += `<td>${c}</td>`);
        html += '</tr>';
    }

    html += '</tbody></table>';
    return html;
}

// 5. Ações de Compartilhamento
btnShareWhatsApp.addEventListener('click', () => {
    if (!lastReportData) return;
    const url = `https://api.whatsapp.com/send?text=${encodeURIComponent(lastReportData.whatsapp_text)}`;
    window.open(url, '_blank');
});

btnShareEmail.addEventListener('click', () => {
    if (!lastReportData) return;
    const mailto = `mailto:?subject=${encodeURIComponent(lastReportData.email_subject)}&body=${encodeURIComponent(lastReportData.email_body)}`;
    window.location.href = mailto;
});

btnCopyReport.addEventListener('click', () => {
    if (!lastReportData) return;
    const reportText = `# ${lastReportData.title}\nDepartamento: ${lastReportData.department}\n\nResumo:\n${lastReportData.summary}\n\nTranscrição:\n${lastReportData.sanitized_transcription}\n\nMatriz RACI:\n${lastReportData.raci_markdown}`;
    navigator.clipboard.writeText(reportText).then(() => {
        alert('Relatório copiado para a área de transferência com sucesso!');
    });
});

// 6. Consultas RAG (BigQuery Vector Search)
btnRagAsk.addEventListener('click', executeRagSearch);
ragInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') executeRagSearch();
});

document.querySelectorAll('.chip').forEach(chip => {
    chip.addEventListener('click', () => {
        ragInput.value = chip.getAttribute('data-q');
        executeRagSearch();
    });
});

async function executeRagSearch() {
    const question = ragInput.value.trim();
    if (!question) return;

    btnRagAsk.disabled = true;
    btnRagAsk.textContent = 'Buscando...';
    ragResponseArea.style.display = 'none';

    try {
        const response = await fetch(`${API_BASE}/api/rag-query`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question: question, top_k: 3 })
        });

        const data = await response.json();
        ragAnswerText.textContent = data.answer;

        ragSourcesList.innerHTML = '';
        (data.sources || []).forEach(s => {
            const li = document.createElement('li');
            li.textContent = `[${s.department || 'Geral'}] ${s.meeting_title} (Falante: ${s.speaker}, Score de Similaridade: ${s.similarity_score})`;
            ragSourcesList.appendChild(li);
        });

        ragResponseArea.style.display = 'block';

    } catch (err) {
        alert(`Erro na busca: ${err.message}`);
        console.error(err);
    } finally {
        btnRagAsk.disabled = false;
        btnRagAsk.textContent = 'Perguntar';
    }
}
